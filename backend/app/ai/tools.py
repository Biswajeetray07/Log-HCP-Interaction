import os
import json
from datetime import datetime
from typing import Union, Dict
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

from app.core.database import SessionLocal
from app.models.interaction import Interaction

llm = ChatGroq(
    api_key=os.environ.get("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile",
    temperature=0
)

# Titles and honorifics to ignore when checking if a name was hallucinated
HONORIFICS = {"dr", "dr.", "mr", "mr.", "ms", "ms.", "prof", "prof."}

# The only sentiment values we allow in the database
VALID_SENTIMENTS = {"Interested", "Neutral", "Not Interested"}


def _parse_llm_json(raw_text: str) -> Dict:
    """Strip markdown fences and parse JSON from LLM output.

    LLMs frequently wrap their JSON in ```json ... ``` blocks,
    so we need to handle that before parsing.
    """
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())


def _normalize_sentiment(raw: str) -> str:
    """Map free-text sentiment to one of the 3 allowed values.

    The LLM prompt already asks for normalized values, but models
    sometimes return variations like 'very interested' or 'not convinced'.
    This is a safety net.
    """
    raw = (raw or "Neutral").strip().lower()
    if "not" in raw or "convinced" in raw:
        return "Not Interested"
    if "interest" in raw:
        return "Interested"
    return "Neutral"


# ---------- TOOL 1: Log Interaction ----------

def log_interaction_tool(input_text: str) -> Union[Dict, str]:
    """Extract structured data from a sales rep's notes and save to the database."""

    prompt = PromptTemplate.from_template(
        "You are a strict data extraction assistant.\n"
        "Input text: {input_text}\n\n"
        "Extract fields and return ONLY a valid JSON object without markdown.\n"
        "RULES:\n"
        "1. DO NOT hallucinate. Only extract names and products explicitly mentioned.\n"
        "2. Resolve pronouns ('he', 'she') to the actual name if possible.\n"
        "Fields:\n"
        "- hcp_name: exact name of the healthcare professional\n"
        "- specialty: null if not mentioned (do not guess)\n"
        "- product: product discussed (null if not mentioned)\n"
        "- interaction_date: date of interaction (e.g. 'Today')\n"
        "- summary: brief summary of the text\n"
        "- sentiment: strictly 'Interested', 'Neutral', or 'Not Interested'. "
        "Map variations ('very interested' -> 'Interested', 'okay' -> 'Neutral', 'not convinced' -> 'Not Interested').\n"
        "- next_action: if not stated, infer from sentiment. MUST include the HCP name and product, "
        "be specific, and be at most 15 words. Never use generic text like 'Follow up with HCP'.\n"
    )

    result = (prompt | llm).invoke({"input_text": input_text})

    try:
        data = _parse_llm_json(result.content)
    except Exception as e:
        return {"status": "error", "message": f"Failed to parse LLM output: {e}"}

    # --- Validation ---

    hcp_name = data.get("hcp_name")
    if not hcp_name:
        return {"status": "error", "message": "Could you please clarify the name of the Healthcare Professional?"}

    # Verify the extracted name actually appears in the input (anti-hallucination)
    name_parts = [p.lower() for p in hcp_name.split() if p.lower() not in HONORIFICS]
    if name_parts and not any(part in input_text.lower() for part in name_parts):
        return {"status": "error", "message": f"Extracted name '{hcp_name}' doesn't appear in the original input. Please verify."}

    if not data.get("product"):
        return {"status": "error", "message": "Could you please specify which product was discussed?"}

    data["sentiment"] = _normalize_sentiment(data.get("sentiment"))

    # --- Persist to database ---

    db = SessionLocal()
    try:
        interaction = Interaction(
            hcp_name=data.get("hcp_name"),
            specialty=data.get("specialty"),
            product=data.get("product"),
            interaction_date=datetime.now(),
            summary=data.get("summary"),
            sentiment=data.get("sentiment"),
            next_action=data.get("next_action")
        )

        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        return {
            "status": "success",
            "message": "Interaction logged successfully",
            "data": {
                "id": interaction.id,
                "hcp_name": interaction.hcp_name,
                "specialty": interaction.specialty,
                "product": interaction.product,
                "interaction_date": interaction.interaction_date.isoformat() if interaction.interaction_date else None,
                "summary": interaction.summary,
                "sentiment": interaction.sentiment,
                "next_action": interaction.next_action
            }
        }

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Database error: {e}"}
    finally:
        db.close()


# ---------- TOOL 2: Edit Interaction ----------

def edit_interaction_tool(input_text: str) -> Union[Dict, str]:
    """Figure out which field the user wants to change and update the most recent interaction."""

    prompt = PromptTemplate.from_template(
        "Extract what field the user wants to update.\n"
        "Return ONLY JSON with keys: action (always 'edit'), field (e.g. sentiment, product), and value (the new value).\n"
        "Valid fields: hcp_name, specialty, product, interaction_date, summary, sentiment, next_action\n"
        "Input text: {input_text}\n"
    )
    result = (prompt | llm).invoke({"input_text": input_text})

    try:
        data = _parse_llm_json(result.content)
    except Exception:
        return {"status": "error", "message": "Could you clarify which field you'd like to edit?"}

    field = data.get("field")
    value = data.get("value")

    if not field or value is None:
        return {"status": "error", "message": "Couldn't determine which field to update or what the new value should be."}

    allowed_fields = ["hcp_name", "specialty", "product", "interaction_date", "summary", "sentiment", "next_action"]
    if field not in allowed_fields:
        return {"status": "error", "message": f"'{field}' is not an editable field."}

    db = SessionLocal()
    try:
        latest = db.query(Interaction).order_by(Interaction.created_at.desc()).first()

        if not latest:
            return {"status": "error", "message": "No interactions found to update."}

        # Handle date parsing separately since it needs type conversion
        if field == "interaction_date":
            try:
                value = datetime.fromisoformat(str(value))
            except ValueError:
                value = datetime.now()

        setattr(latest, field, value)
        db.commit()

        return {
            "status": "success",
            "message": f"Updated {field} successfully.",
            "data": {"updated_field": field, "new_value": value}
        }

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Database error: {e}"}
    finally:
        db.close()


# ---------- TOOL 3: Fetch Interaction ----------

def fetch_interaction_tool(input_text: str) -> Union[Dict, str]:
    """Look up the most recent interaction for a given HCP by name."""

    prompt = PromptTemplate.from_template(
        "Extract the HCP name the user wants to retrieve data for.\n"
        "Return ONLY JSON with keys: action (always 'fetch') and hcp_name.\n"
        "Input text: {input_text}\n"
    )
    result = (prompt | llm).invoke({"input_text": input_text})

    try:
        data = _parse_llm_json(result.content)
        hcp_name = data.get("hcp_name")
        if not hcp_name:
            return {"status": "error", "message": "Which Healthcare Professional are you looking for?"}
    except Exception:
        return {"status": "error", "message": "Which Healthcare Professional are you looking for?"}

    db = SessionLocal()
    try:
        # Case-insensitive partial match so "Sharma" finds "Dr Sharma"
        interaction = (
            db.query(Interaction)
            .filter(Interaction.hcp_name.ilike(f"%{hcp_name}%"))
            .order_by(Interaction.created_at.desc())
            .first()
        )

        if not interaction:
            return {"status": "error", "message": f"No interactions found for {hcp_name}."}

        return {
            "status": "success",
            "message": f"Found interaction for {hcp_name}.",
            "data": {
                "hcp_name": interaction.hcp_name,
                "product": interaction.product,
                "summary": interaction.summary,
                "sentiment": interaction.sentiment,
                "next_action": interaction.next_action
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Database error: {e}"}
    finally:
        db.close()


# ---------- TOOL 4: Suggest Next Action ----------

def suggest_next_action_tool(input_text: str) -> Dict:
    """Generate a concise, actionable next step for the sales rep."""

    prompt = PromptTemplate.from_template(
        "Based on the interaction context, suggest a short, actionable next step for the sales rep.\n"
        "Example: 'Follow up with Dr Mehta and provide product samples.'\n\n"
        "Input: {input_text}\n"
        "Suggestion:"
    )
    result = (prompt | llm).invoke({"input_text": input_text})
    return {
        "status": "success",
        "message": "Next action suggestion",
        "data": {"suggestion": result.content.strip()}
    }


# ---------- TOOL 5: HCP Insights ----------

def hcp_insights_tool(input_text: str) -> Dict:
    """Generate a marketing insight about the referenced HCP."""

    prompt = PromptTemplate.from_template(
        "Generate a brief, realistic marketing insight about the HCP mentioned below.\n"
        "Example: 'Dr Sharma shows strong interest in cardiovascular products.'\n\n"
        "Input: {input_text}\n"
        "Insight:"
    )
    result = (prompt | llm).invoke({"input_text": input_text})
    return {
        "status": "success",
        "message": "HCP insight generated",
        "data": {"insight": result.content.strip()}
    }
