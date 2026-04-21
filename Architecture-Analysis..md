# AI-First CRM HCP Module — Architecture & Knowledge Analysis

## 1. Project Overview

**What we're building**: A "Log Interaction Screen" for an AI-first CRM system focused on Healthcare Professional (HCP) engagement. Field reps in life sciences use this to log their interactions with doctors/HCPs — either via a **structured form** or a **conversational chat** powered by a LangGraph AI agent.

**Why it matters**: Traditional CRMs force rigid form-filling. An AI-first approach lets reps simply *describe* what happened in natural language, and the AI extracts structured data, suggests next steps, and provides insights.

---

## 2. Tech Stack Summary

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Frontend** | React + Redux Toolkit | Google Inter font, dual UI (form + chat) |
| **Backend** | Python + FastAPI | REST APIs + `/chat` endpoint for agent |
| **AI Agent** | LangGraph | Graph-based agent with 5 tools |
| **LLM** | Groq API → `gemma2-9b-it` | Fast inference; `llama-3.3-70b-versatile` as fallback |
| **Database** | PostgreSQL | Interaction records, HCP metadata |

---

## 3. Data Model Design

### 3.1 `hcp_profiles` Table
```sql
CREATE TABLE hcp_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    specialty VARCHAR(255),
    institution VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 3.2 `interactions` Table
```sql
CREATE TABLE interactions (
    id SERIAL PRIMARY KEY,
    hcp_id INTEGER REFERENCES hcp_profiles(id),
    hcp_name VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    time TIME,
    channel VARCHAR(50) NOT NULL,          -- 'in-person', 'phone', 'email', 'video'
    product_discussed VARCHAR(255),
    notes TEXT,
    summary TEXT,                           -- AI-generated summary
    sentiment VARCHAR(20),                  -- 'positive', 'neutral', 'negative'
    follow_up_date DATE,
    follow_up_action TEXT,
    key_topics JSONB,                       -- extracted topics array
    outcome VARCHAR(100),                   -- 'sample_requested', 'follow_up_needed', etc.
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

> [!NOTE]
> The `summary`, `sentiment`, `key_topics` fields are populated by the LLM during the **Log Interaction** tool execution. The `notes` field holds the raw rep input.

---

## 4. API Design

### 4.1 CRUD APIs (Milestone 1)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/interactions` | Create a new interaction |
| `GET` | `/api/interactions` | List all interactions (with filters) |
| `GET` | `/api/interactions/{id}` | Get single interaction |
| `PUT` | `/api/interactions/{id}` | Update an interaction |
| `DELETE` | `/api/interactions/{id}` | Delete an interaction |
| `GET` | `/api/hcps` | List HCP profiles |
| `POST` | `/api/hcps` | Create HCP profile |

### 4.2 Chat API (Milestone 4)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/chat` | Send message → LangGraph agent → response |

**Request body**:
```json
{
  "message": "I met Dr. Smith today at Apollo Hospital...",
  "session_id": "optional-session-id"
}
```

**Response**:
```json
{
  "response": "I've logged your interaction with Dr. Smith. Here's what I captured...",
  "tool_used": "log_interaction",
  "data": { ... },
  "session_id": "abc-123"
}
```

---

## 5. LangGraph Agent Architecture

### 5.1 Agent Graph Design

```
User Message
     │
     ▼
┌─────────────┐
│  LLM Node   │ ← Groq gemma2-9b-it
│  (Classify  │
│   Intent)   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Router    │ ← Routes to appropriate tool
│    Node     │
└──────┬──────┘
       │
       ├──► log_interaction
       ├──► edit_interaction
       ├──► fetch_interaction
       ├──► suggest_next_action
       └──► hcp_insights
              │
              ▼
       ┌─────────────┐
       │  Response    │ ← Format & return to user
       │  Formatter   │
       └─────────────┘
```

### 5.2 The Five Tools

#### Tool 1: `log_interaction` (Required)
- **Trigger**: User describes a meeting/call with an HCP
- **What it does**:
  1. LLM extracts entities: HCP name, date, channel, products, topics
  2. LLM generates a concise summary
  3. LLM performs sentiment analysis
  4. Inserts structured record into `interactions` table
- **Example input**: *"I visited Dr. Priya Sharma at Max Hospital today. We discussed Cardizem and she seemed very interested. She asked for samples and wants a follow-up next week."*
- **Extracted data**: `{hcp_name: "Dr. Priya Sharma", channel: "in-person", product: "Cardizem", sentiment: "positive", outcome: "sample_requested", follow_up: "next week"}`

#### Tool 2: `edit_interaction` (Required)
- **Trigger**: User wants to modify a previously logged interaction
- **What it does**:
  1. Identifies which interaction to edit (by ID, HCP name, or date)
  2. LLM determines which fields to update
  3. Updates the record in DB
- **Example input**: *"Update my last interaction with Dr. Sharma — change the product to Diltiazem instead of Cardizem"*

#### Tool 3: `fetch_interaction`
- **Trigger**: User asks to see/retrieve interactions
- **What it does**:
  1. Parses query filters (HCP name, date range, etc.)
  2. Queries DB and returns formatted results
- **Example input**: *"Show me all interactions with Dr. Sharma from last month"*

#### Tool 4: `suggest_next_action`
- **Trigger**: User asks "what should I do next?" or after logging
- **What it does**:
  1. Analyzes recent interactions with an HCP
  2. LLM generates suggested next steps
  3. Considers follow-up dates, sentiment trends, products
- **Example output**: *"Based on your last 3 interactions with Dr. Sharma, she's shown increasing interest in Cardizem. Recommend scheduling a product demo within the next 5 days."*

#### Tool 5: `hcp_insights`
- **Trigger**: User asks for HCP profile/engagement summary
- **What it does**:
  1. Aggregates all interactions for an HCP
  2. LLM generates an engagement summary
  3. Shows interaction frequency, preferred channels, sentiment trends
- **Example output**: *"Dr. Sharma: 8 interactions in Q1. Primary interest: Cardiology products. Sentiment trend: Improving. Preferred channel: In-person."*

---

## 6. Milestone-by-Milestone Blueprint

### Milestone 1 — Backend Foundation
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, CORS, router includes
│   ├── config.py             # Settings (DB URL, Groq key, etc.)
│   ├── database.py           # SQLAlchemy engine + session
│   ├── models.py             # SQLAlchemy ORM models
│   ├── schemas.py            # Pydantic request/response schemas
│   └── routers/
│       ├── __init__.py
│       ├── interactions.py   # CRUD endpoints
│       └── hcps.py           # HCP endpoints
├── requirements.txt
├── .env
└── alembic/ (optional)
```

**Key decisions**:
- Use **SQLAlchemy** as ORM with **asyncpg** for async PostgreSQL
- Use **Pydantic v2** schemas for validation
- CORS enabled for React frontend (localhost:3000 → localhost:8000)

### Milestone 2 — LangGraph Agent Core
```
backend/
├── app/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py          # LangGraph graph definition
│   │   ├── state.py          # Agent state schema
│   │   ├── nodes.py          # LLM node, router node, response node
│   │   └── tools.py          # 5 tool definitions (mock first)
│   └── services/
│       └── llm.py            # Groq client wrapper
```

**Key decisions**:
- Use `langchain-groq` for LLM integration
- Agent state carries: `messages`, `current_tool`, `tool_result`, `session_id`
- Tools are decorated with `@tool` from langchain
- Router uses LLM function-calling to pick the right tool

### Milestone 3 — Tool + DB Integration
- Replace mock tool functions with real DB operations
- Add LLM extraction pipeline in `log_interaction`:
  1. Call LLM with extraction prompt → get structured JSON
  2. Validate with Pydantic
  3. Insert into DB
- Add query building in `fetch_interaction`

### Milestone 4 — API + Agent Integration
- Create `/api/chat` endpoint
- Wire: HTTP request → LangGraph `graph.invoke()` → HTTP response
- Add session management (in-memory dict or Redis)

### Milestone 5 — Frontend
```
frontend/
├── public/
├── src/
│   ├── app/
│   │   └── store.js          # Redux store
│   ├── features/
│   │   ├── chat/
│   │   │   ├── chatSlice.js
│   │   │   └── ChatUI.jsx
│   │   ├── form/
│   │   │   ├── formSlice.js
│   │   │   └── FormUI.jsx
│   │   └── interactions/
│   │       ├── interactionSlice.js
│   │       └── InteractionList.jsx
│   ├── services/
│   │   └── api.js            # Axios/fetch wrappers
│   ├── components/           # Shared UI components
│   ├── App.jsx
│   ├── index.css
│   └── main.jsx
├── package.json
└── vite.config.js
```

**Key decisions**:
- **Vite** as build tool (fast, modern)
- **Redux Toolkit** with `createAsyncThunk` for API calls
- Two main views: **Chat UI** (conversational) and **Form UI** (structured)
- Tab or toggle to switch between modes
- Google Inter font via Google Fonts CDN

### Milestone 6 — Polish
- Error handling (missing fields, ambiguous edits)
- Loading states, toast notifications
- Clean AI response formatting
- Demo script preparation

---

## 7. Key Integration Points

```mermaid
flowchart LR
    A[React Frontend] -->|REST API| B[FastAPI Backend]
    A -->|POST /api/chat| B
    B -->|CRUD| C[(PostgreSQL)]
    B -->|invoke| D[LangGraph Agent]
    D -->|tools| C
    D -->|LLM calls| E[Groq API]
    E -->|gemma2-9b-it| D
```

## 8. Important Patterns to Follow

### 8.1 LLM Prompting Strategy
- **System prompt**: Define the agent as a Life Sciences CRM assistant for field reps
- **Entity extraction**: Use structured output prompts with JSON schema
- **Summarization**: Keep summaries under 100 words, action-oriented
- **Sentiment**: Classify as positive/neutral/negative with confidence

### 8.2 Error Handling
- If LLM can't extract required fields → ask user for clarification
- If DB operation fails → return friendly error, log details
- If tool selection is ambiguous → default to asking user

### 8.3 State Management (Redux)
- `chatSlice`: messages array, loading state, session ID
- `formSlice`: form field values, validation errors
- `interactionSlice`: interactions list, selected interaction, filters

---

## 9. Environment Variables Needed

```env
# Backend (.env)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/hcp_crm
GROQ_API_KEY=gsk_xxxxxxxxxxxxx
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Frontend (.env)
VITE_API_BASE_URL=http://localhost:8000/api
```

---

## 10. Evaluation Criteria Awareness

The assignment will be judged on:
1. ✅ **LangGraph + LLM usage** — Must use LangGraph, not raw API calls
2. ✅ **5 working tools** — All demonstrated in video
3. ✅ **Dual UI** — Both form AND chat interfaces
4. ✅ **Code flow explanation** — Clean, understandable architecture
5. ✅ **README.md** — Clear setup instructions
6. ✅ **Video** — 10-15 min walkthrough

> [!IMPORTANT]
> The assignment explicitly states: "If langgraph and LLM are not used, the task will not be accepted." This is non-negotiable.
