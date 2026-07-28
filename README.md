# AION — Artificial Intelligence Organizational Nervous System

A complete organization-management platform: 1 admin, 6 departments, 10 people each
(1 head + 9), role-scoped dashboards, leave approvals, per-department AI agents,
two-way messaging with file attachments, and a live knowledge graph.

## What's inside
- `finals-backend/` — FastAPI backend (Python), runs on **port 8001**.
- `substance-lab/` — the website (plain HTML + JS), runs on **port 5500**.
- Mock data for a demo company ("Nova Robotics") is already in `finals-backend/data/aion.db`.

## Run it (two terminals)

### 1) Backend (port 8001)
```
cd finals-backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

### 2) Frontend (port 5500)
```
cd substance-lab
python -m http.server 5500
```
Then open **http://localhost:5500** in a browser.

## Logging in
Every demo account uses the password **`DemoPass123!`**

| Role | Example login |
|---|---|
| Admin | `demo@aion.ai` |
| Department head (Finance) | `grace.osei@novarobotics.ai` |
| Employee (Finance) | `priya.raman@novatech.example` |

Each of the 61 people signs in to their own dashboard:
- **Employee** — their department (people, projects, policies), their leave, sending
  requests to their head, messaging their head, and their department's AI agent.
- **Department head** — all of the above plus their team's approvals, the department's
  knowledge graph, Finance (if Finance), cross-department messaging, and an org overview.
- **Admin** — the whole organization: overall growth, every department with drill-down,
  all approvals, and the organisation-wide AI agent.

## Notes
- **Secrets removed for sharing.** `finals-backend/.env` has had its keys blanked and its
  signing secrets replaced with placeholders. Before any real use, set your own
  `SECRET_KEY` and `JWT_SECRET_KEY`.
- **AI agents (optional).** The per-department agents and document AI use Groq. Add your own
  key to `.env` as `GROQ_API_KEY=...` to enable them. Without a key, the app still runs — the
  dashboards, logins, messaging, approvals and knowledge graph all work; only the chat-style
  AI replies fall back to a simpler mode.
- The frontend expects the backend at `http://localhost:8001`. To point elsewhere, set
  `window.AION_API_BASE` before `assets/api.js` loads.
