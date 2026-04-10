# Meridian HR Agent — Implementation Plan

## Milestone Summary

| Phase | Days | Deliverable |
|---|---|---|
| 1. Scaffold | 1–2 | Repo, DB, Docker running |
| 2. Mock Data | 2–3 | HRIS + policy data ingested |
| 3. Skills | 3–5 | All 6 tools working in isolation |
| 4. Agent | 5–7 | Both workflows running end-to-end |
| 5. API | 7–9 | REST endpoints for all agent actions |
| 6. Frontend | 9–12 | Dashboard + chat UI connected to API |
| 7. Polish | 12–14 | Full demo-ready system |

---

## Phase 1 — Project Scaffold & Infrastructure (Days 1–2)

**Goal:** Get the repo structure, tooling, and environment wired up before writing any real logic.

1. Initialize repo structure: `backend/`, `frontend/`, `agent/`, `data/`, `scripts/`
2. Set up Python project — `pyproject.toml`, virtual environment, `requirements.txt` with FastAPI, SQLAlchemy, Supabase client, Anthropic SDK
3. Set up Vite + React + TypeScript frontend project
4. Configure environment variables (`.env.example`) — Claude API key, Supabase URL/key, email config
5. Set up Supabase project — create database, enable pgvector extension
6. Write and run initial DB migrations — create the five core tables: `employees`, `onboarding_progress`, `escalations`, `policy_documents`, `agent_actions`
7. Set up Docker — `Dockerfile` for backend, `docker-compose.yml` for local dev
8. Wire up a minimal FastAPI app with a `/health` endpoint to confirm everything boots

---

## Phase 2 — Mock Data Layer (Days 2–3)

**Goal:** Build the fake HRIS and policy data the agent will work against throughout development.

1. Create mock HRIS JSON — 5–10 employee records with realistic fields (name, email, dept, title, manager, hire date)
2. Create mock calendar data — available slots per employee
3. Write 3–5 HR policy documents in markdown — benefits, remote work, I9/W4, PTO, code of conduct
4. Build `DataService` class that reads these JSON/markdown files and exposes clean Python interfaces
5. Write a policy ingestion script — chunk policy docs (500–1000 token sliding window) and store chunks in Supabase `policy_documents` table
6. Confirm data is queryable via SQLAlchemy before moving on

---

## Phase 3 — Skills Framework & Tools (Days 3–5)

**Goal:** Build the six tools the agent can call. Each is a `ClaudeSkill` subclass with a tested `execute()` method.

1. Define the base `ClaudeSkill` abstract class — `name`, `description`, `parameters` schema, `execute()` interface
2. Implement `send_email` skill — mock email delivery (log to console/file), return structured result
3. Implement `schedule_meeting` skill — check mock calendar, pick open slot, return meeting object
4. Implement `lookup_employee` skill — query mock HRIS, return employee record
5. Implement `update_onboarding_progress` skill — update `onboarding_progress` table in Supabase
6. Implement `flag_for_human_review` skill — write to `escalations` table, mock HR email notification
7. Implement `retrieve_policy` skill — embed the query via Claude Embeddings API, run pgvector similarity search, return top chunks with confidence scores
8. Write a tool registry that maps skill names to their JSON schemas (used to pass `tools` to Claude API)
9. Test each skill in isolation with sample inputs

---

## Phase 4 — Agent Orchestrator (Days 5–7)

**Goal:** Build the core agentic loop that drives both workflows.

1. Build `OnboardingAgent` in `agent/orchestrator.py` — accepts trigger event, holds skill registry, drives the tool-use loop
2. Implement the agentic loop — send messages to Claude API with `tools`, parse `tool_use` blocks, dispatch to skill registry, feed results back as `tool_result`, repeat until `end_turn`
3. Implement the **autonomous onboarding workflow** — on `new_hire_created` event: welcome email → schedule meeting → send paperwork → track progress → escalate I9
4. Implement the **policy Q&A workflow** — receive question → call `retrieve_policy` → check confidence threshold → respond or escalate
5. Add the I9 hard rule — `flag_for_human_review` always fires for I9, regardless of confidence
6. Log every tool call as a structured record to the `agent_actions` audit table
7. Add confidence threshold logic — if `retrieve_policy` returns score < 0.7, route to escalation instead of answering
8. Test both workflows end-to-end with mock data (no frontend yet)

---

## Phase 5 — FastAPI Backend (Days 7–9)

**Goal:** Expose the agent and data via a REST API the frontend can call.

1. `POST /onboarding/trigger` — accepts new hire payload, fires the onboarding agent asynchronously
2. `GET /onboarding/{employee_id}` — returns current onboarding progress state
3. `GET /onboarding` — returns all active onboardings (for dashboard)
4. `POST /chat` — accepts `{question, employee_id}`, runs policy Q&A workflow, returns agent response
5. `GET /escalations` — returns open escalation queue
6. `PATCH /escalations/{id}` — resolve or reject an escalation (HR admin action)
7. `GET /audit-log` — returns paginated agent action history
8. Add request validation with Pydantic models for all endpoints
9. Add error handling — tool failures should return structured errors, not 500s

---

## Phase 6 — Frontend Dashboard (Days 9–12)

**Goal:** Build the HR admin UI and new hire chat interface.

1. Set up React project with routing — `/dashboard`, `/escalations`, `/audit`, `/chat`
2. Build **Onboarding Dashboard** — card grid showing each new hire's progress, step status (sent/pending/escalated), overall status badge
3. Build **Escalation Queue** — list view of open escalations, context about why it escalated, approve/reject buttons that call `PATCH /escalations/{id}`
4. Build **Audit Log** — paginated table of agent actions with timestamp, action type, employee, result
5. Build **Policy Chat Interface** — text input, message thread, agent responses with confidence indicator, "Connect with HR" fallback button
6. Wire all components to the FastAPI backend
7. Add loading states and basic error handling in the UI
8. Style for readability — clean, functional, non-technical-user friendly (Tailwind or similar)

---

## Phase 7 — Integration Testing & Polish (Days 12–14)

**Goal:** Run the full system end-to-end, fix edge cases, and get it demo-ready.

1. Run full onboarding workflow from trigger → dashboard update → escalation resolution
2. Run policy Q&A — high confidence path, low confidence path (escalation), unknown topic path
3. Verify the I9 hard-escalation rule fires every time
4. Verify all agent actions are appearing in the audit log
5. Test error paths — what happens when a tool fails mid-workflow
6. Write a `seed.py` script that populates mock data and triggers a demo onboarding automatically
7. Clean up environment variable handling, remove hardcoded values
8. Write `README.md` setup instructions — how to run locally with Docker, how to trigger the agent, how to use the dashboard

---

> **Critical path:** Phases 3 → 4 are the foundation. Everything else (API, frontend) wraps around a working agent. Do not start Phase 5 until the agent orchestrator can run both workflows successfully against mock data.
