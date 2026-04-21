import os
import json
from typing import TypedDict, Optional, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, START, END

from app.ai.tools import (
    log_interaction_tool,
    edit_interaction_tool,
    fetch_interaction_tool,
    suggest_next_action_tool,
    hcp_insights_tool
)

llm = ChatGroq(
    api_key=os.environ.get("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile",
    temperature=0
)

# Lightweight conversational memory — tracks the last HCP discussed so
# follow-up messages like "update that" or "what about last meeting?" work.
memory = {
    "last_hcp_name": None,
    "last_intent": None
}

INTENT_TO_TOOL = {
    "log": log_interaction_tool,
    "edit": edit_interaction_tool,
    "fetch": fetch_interaction_tool,
    "suggest": suggest_next_action_tool,
    "insights": hcp_insights_tool,
}


class AgentState(TypedDict):
    input_text: str
    original_input: str
    intent: Optional[str]
    tool_to_use: Optional[str]
    response: Any


# --- Graph Nodes ---

def capture_input(state: AgentState) -> AgentState:
    """Preserve the raw input before any context gets prepended."""
    raw = state.get("input_text", "").strip()
    return {"input_text": raw, "original_input": raw}


def inject_memory(state: AgentState) -> AgentState:
    """Prepend prior HCP context so the classifier can resolve references
    like 'update that' or 'what about last meeting?'"""
    prefix = ""
    if memory["last_hcp_name"]:
        prefix = f"[Context: The user previously discussed '{memory['last_hcp_name']}'] "
    return {"input_text": prefix + state["input_text"]}


def classify_intent(state: AgentState) -> AgentState:
    """Use the LLM to classify the user's message into one of our tool categories."""
    prompt = PromptTemplate.from_template(
        "You are an intent classifier for a CRM system. Classify the user's input STRICTLY into EXACTLY ONE of these categories: "
        "['log', 'edit', 'fetch', 'suggest', 'insights', 'unknown'].\n\n"
        "EXAMPLES:\n"
        "- 'Met Dr Sharma...' -> log\n"
        "- 'Update sentiment...' -> edit\n"
        "- 'What did I discuss with Dr Mehta?' -> fetch\n"
        "- 'What should I do next?' -> suggest\n"
        "- 'Give insights...' -> insights\n\n"
        "RULES:\n"
        "1. Return ONLY the intent label (no explanation).\n"
        "2. Queries asking for past information ('What did I discuss...') are ALWAYS 'fetch', never 'log'.\n"
        "3. Anything unrelated to healthcare or sales ('Tell me a joke') is ALWAYS 'unknown'.\n\n"
        "Input: {input_text}\n"
        "Intent:"
    )
    result = (prompt | llm).invoke({"input_text": state["input_text"]})
    raw_label = result.content.strip().lower()

    # Extract the first valid intent found in the LLM's response
    intent = "unknown"
    for candidate in INTENT_TO_TOOL:
        if candidate in raw_label:
            intent = candidate
            break

    return {"intent": intent}


def route_to_tool(state: AgentState) -> AgentState:
    """Map the classified intent to a tool name (or 'none' for unknown)."""
    intent = state.get("intent", "unknown")
    print(f"[Agent] Intent: {intent}")

    tool_name = intent if intent in INTENT_TO_TOOL else "none"
    return {"tool_to_use": tool_name}


def execute_tool(state: AgentState) -> AgentState:
    """Run the selected tool and update conversational memory."""
    global memory

    tool_name = state.get("tool_to_use", "none")

    if tool_name == "none":
        return {"response": {"status": "error", "message": "This system is for HCP interactions only. Try logging an interaction or fetching past data."}}

    tool_fn = INTENT_TO_TOOL[tool_name]
    response = tool_fn(state.get("input_text", ""))

    # Update memory so future messages have context
    memory["last_intent"] = state.get("intent")
    if isinstance(response, dict):
        data = response.get("data", {})
        hcp = data.get("hcp_name") if isinstance(data, dict) else None
        if hcp:
            memory["last_hcp_name"] = hcp

    return {"response": response}


def format_response(state: AgentState) -> AgentState:
    """Final passthrough — exists as an explicit output node for the graph."""
    return {"response": state.get("response")}


# --- Build the LangGraph pipeline ---

workflow = StateGraph(AgentState)

workflow.add_node("capture_input", capture_input)
workflow.add_node("inject_memory", inject_memory)
workflow.add_node("classify_intent", classify_intent)
workflow.add_node("route_to_tool", route_to_tool)
workflow.add_node("execute_tool", execute_tool)
workflow.add_node("format_response", format_response)

workflow.add_edge(START, "capture_input")
workflow.add_edge("capture_input", "inject_memory")
workflow.add_edge("inject_memory", "classify_intent")
workflow.add_edge("classify_intent", "route_to_tool")
workflow.add_edge("route_to_tool", "execute_tool")
workflow.add_edge("execute_tool", "format_response")
workflow.add_edge("format_response", END)

agent = workflow.compile()


def run_agent(user_input: str) -> Any:
    """Entry point for the /chat endpoint. Runs the full agent pipeline."""
    result = agent.invoke({"input_text": user_input})
    return result.get("response", "Error processing request")


if __name__ == "__main__":
    print("Running agent test sequence...\n")

    test_messages = [
        "Met Dr. Sharma today, discussed diabetes drug",
        "update that, he was highly interested",
        "what about last meeting?",
    ]

    for msg in test_messages:
        print(f"User: {msg}")
        res = run_agent(msg)
        if isinstance(res, dict):
            print(f"Agent:\n{json.dumps(res, indent=2)}\n")
        else:
            print(f"Agent:\n{res}\n")
