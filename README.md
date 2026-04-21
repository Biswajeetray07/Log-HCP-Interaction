# AI-First CRM — HCP Interaction Module

A CRM tool for pharma sales reps to log, track, and analyze interactions with healthcare professionals. Instead of filling out traditional forms, reps can describe their meetings in plain English — the AI agent handles the rest.

## Why build it this way?

Most CRM systems treat data entry as a chore. Sales reps spend time filling forms after every meeting, which leads to incomplete data or entries that never get made.

This project flips that around. The core idea: **talk to the CRM like you'd talk to a colleague.** Say "Met Dr Sharma today, discussed insulin, he was interested" and the system extracts the structured data, validates it, and saves it to PostgreSQL — no forms needed.

There's still a form mode for people who prefer it, but the form can also auto-fill itself from chat data, so the two modes work together.

## How it works

```
User message → FastAPI /chat → LangGraph Agent → Tool execution → PostgreSQL → Response
```

The backend runs a **LangGraph state graph** — not a simple chain, but an actual multi-node pipeline with distinct responsibilities:

1. **Capture input** — store the raw message
2. **Inject memory** — prepend context from the last conversation (so "update that" actually works)
3. **Classify intent** — LLM decides whether the user wants to log, edit, fetch, get a suggestion, or get insights
4. **Route** — maps the intent to the correct tool function
5. **Execute** — runs the tool, hits the database if needed
6. **Respond** — returns a standardized `{status, message, data}` payload

### Why LangGraph instead of a regular LangChain chain?

Because the flow has distinct steps with different concerns — memory injection happens before classification, routing is deterministic after classification, and tool execution has side effects (DB writes). A StateGraph makes this explicit instead of hiding it in a single prompt.

### Why Groq?

Speed. Groq's inference is fast enough that the round-trip feels conversational rather than waiting for an LLM to think. The system uses `llama-3.3-70b-versatile` for its strong instruction-following and JSON extraction abilities.

## What the AI agent can do

| Tool | What it does |
|---|---|
| **Log** | Extracts HCP name, product, sentiment, and next steps from natural language, then saves to DB |
| **Edit** | Detects which field you want to change and updates the most recent interaction |
| **Fetch** | Looks up past interactions by HCP name (fuzzy matching) |
| **Suggest** | Generates a specific, actionable next step based on conversation context |
| **Insights** | Produces a marketing insight about a particular HCP |

### Built-in guardrails

- **Anti-hallucination**: extracted names are checked against the original input. If the LLM makes up a name, it gets caught.
- **Sentiment normalization**: "very interested", "highly interested", "keen" all map to `Interested`. Only 3 values reach the database.
- **Intent rejection**: off-topic queries like "tell me a joke" get a polite rejection instead of being forced into a tool.
- **JSON safety net**: LLM output is stripped of markdown fences before parsing.

## Tech stack

| What | Why |
|---|---|
| **FastAPI** | Async-capable, auto-generates OpenAPI docs, clean dependency injection for DB sessions |
| **LangGraph** | Explicit state management for multi-step agent flows. Better than cramming everything into one prompt |
| **Groq (llama-3.3-70b-versatile)** | Fast inference, strong at structured extraction and following strict output formats |
| **PostgreSQL + SQLAlchemy** | Battle-tested relational store. SQLAlchemy gives us an ORM without losing control |
| **React + Redux Toolkit** | Component architecture for the UI, centralized state so chat history and form data stay in sync |
| **Tailwind CSS** | Utility-first styling. Keeps the dark-mode UI consistent without maintaining a separate stylesheet |
| **Vite** | Fast dev server with HMR. No build config to maintain |

## Project structure

```
backend/
├── app/
│   ├── ai/
│   │   ├── agent.py           # LangGraph pipeline definition
│   │   └── tools.py           # The 5 tool implementations
│   ├── api/routes/
│   │   ├── chat.py            # POST /chat (main entry point)
│   │   └── interaction.py     # REST CRUD for interactions
│   ├── core/
│   │   ├── config.py          # Env var loading
│   │   └── database.py        # SQLAlchemy setup
│   ├── models/interaction.py  # DB schema
│   └── schemas/interaction.py # Pydantic models
├── main.py                    # FastAPI app
└── requirements.txt

frontend/
├── src/
│   ├── app/store.js           # Redux store
│   ├── components/
│   │   ├── chat/              # ChatWindow, ChatInput, ChatMessage
│   │   ├── form/              # InteractionForm
│   │   └── layout/            # Navbar
│   ├── features/chat/chatSlice.js
│   ├── pages/Home.jsx         # Mode toggle (Chat / Form)
│   └── services/api.js        # fetch wrapper for /chat
└── package.json
```

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL running locally
- A Groq API key ([console.groq.com](https://console.groq.com))

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

Create the database:
```sql
CREATE DATABASE hcp_crm;
```

Create `backend/.env`:
```
GROQ_API_KEY=your_key_here
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/hcp_crm
```

Start the server:
```bash
python main.py
# → http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## API

All interaction goes through one endpoint:

### `POST /chat`

```json
// Request
{ "message": "Met Dr Sharma, discussed insulin, very interested" }

// Response
{
  "response": {
    "status": "success",
    "message": "Interaction logged successfully",
    "data": {
      "id": 1,
      "hcp_name": "Dr Sharma",
      "specialty": null,
      "product": "insulin",
      "sentiment": "Interested",
      "next_action": "Follow up with Dr Sharma to discuss insulin benefits"
    }
  }
}
```

Every tool returns the same shape: `{status, message, data}`. Errors use `status: "error"` with a human-readable `message`.

There are also standard REST endpoints at `/interactions/` for direct CRUD, but the chat endpoint is the primary interface.

## Example workflows

**Log → Fetch → Edit (conversational memory)**
```
You: "Met Dr Sharma, discussed insulin, very interested"
Agent: logs interaction, returns structured data

You: "What did I discuss with Dr Sharma?"
Agent: fetches from DB, returns product + sentiment + summary

You: "Update sentiment to neutral"
Agent: updates the most recent interaction's sentiment field
```

**Form auto-fill**
1. Log something via Chat Mode
2. Switch to Form Mode
3. Fields auto-populate from the last structured AI response
4. "✨ Auto-filled by AI" badge appears
5. Edit anything and re-submit

**Edge case handling**
```
You: "Met doctor today"           → "Could you clarify the name?"
You: "Tell me a joke"             → "This system is for HCP interactions only."
You: "Update sentiment"           → edits most recent interaction (uses memory)
```

## Known limitations

- **Memory is process-local**: the `memory` dict lives in the Python process. It resets on server restart and doesn't isolate between users. Fine for a single-user demo, not for production.
- **Edits always target the latest interaction**: there's no way to say "edit the interaction from two weeks ago." It always updates the most recent row.
- **No authentication**: anyone who can reach the API can use it.
- **No migration tool**: tables are created via `create_all()` on startup. For a production app, you'd want Alembic.
- **LLM output is non-deterministic**: the same input might produce slightly different JSON. The parsing and validation layers handle most variations, but edge cases exist.

## What I'd add next

1. **Per-user sessions** — Redis or session tokens so memory is scoped per user
2. **Conversation history** — persist the full chat log, not just the last HCP name
3. **Multi-interaction editing** — "update Dr Sharma's interaction from last Tuesday"
4. **Streaming responses** — WebSocket or SSE so the agent's output appears progressively
5. **Proper tests** — pytest with mocked LLM responses so CI doesn't depend on Groq
6. **Docker Compose** — one-command setup for backend + frontend + Postgres

---

Built with FastAPI, LangGraph, React, and Groq.