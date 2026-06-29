# Meridian HR Agent

An autonomous AI agent that handles new hire onboarding and policy Q&A for HR teams. Built on the Claude API with native tool use, a FastAPI backend, Supabase (PostgreSQL + pgvector), and a React dashboard.

## Overview

Meridian is an **agent layer**, not a system of record — it sits on top of an HRIS rather than replacing it. It runs two workflows:

**Autonomous Onboarding** — When a new hire is created, the agent independently sends a welcome email, schedules the onboarding meeting track, delivers paperwork, tracks step-by-step progress, and escalates compliance items (I-9 verification) to HR for human sign-off. HR never kicks anything off manually; the dashboard, escalation queue, and audit log are read-only views into work the agent already did.

**Policy Q&A** — New hires ask plain-language questions about company policy. The agent answers via RAG over the employee handbook with a confidence score attached to every response. Low-confidence or judgment-dependent answers escalate to HR instead of guessing.

## How It Works

The agent is built on **composable Claude Skills** — small, isolated modules with clear input/output contracts that the model invokes as tools. Six skills cover the full surface:

| Skill | Purpose |
|---|---|
| `send_email` | Welcome email + paperwork delivery |
| `schedule_meeting` | Books onboarding meetings against contact availability, conflict-aware |
| `lookup_employee` | Reads the HRIS, filtered to safe fields (no salary/SSN) |
| `retrieve_policy` | pgvector similarity search over handbook chunks; returns docs + confidence + `should_escalate` |
| `flag_for_human_review` | Writes an escalation record and notifies HR |
| `update_onboarding_progress` | Upserts per-step onboarding state |

A single `OnboardingAgent` drives an agentic tool-use loop — the model plans, calls skills, reads results, and repeats until done. Both workflows share one loop, differing only by system prompt. Two guarantees live in deterministic Python *outside* the model's reasoning: **I-9 always escalates** regardless of confidence, and **answers below the confidence threshold always route to HR**. Compliance is a hard rule, not a probability.

Every tool call is logged as a structured record to an `agent_actions` audit table — a complete, queryable audit trail.

## Architecture

```
HRIS webhook
        │
        ▼
┌─────────────────────┐      ┌──────────────────────────┐
│  FastAPI backend    │─────▶│  OnboardingAgent          │
│  REST endpoints     │      │  (Claude tool-use loop)   │
└─────────────────────┘      └────────────┬─────────────┘
        │                                 │
        │                    ┌────────────▼─────────────┐
        │                    │  6 Claude Skills (tools) │
        │                    └────────────┬─────────────┘
        ▼                                 ▼
┌─────────────────────────────────────────────────────────┐
│  Supabase (PostgreSQL + pgvector)                        │
│  onboarding_progress · escalations · policy_documents    │
│  · agent_actions (audit log)                             │
└─────────────────────────────────────────────────────────┘
        ▲
        │
┌─────────────────────┐
│  React frontend     │
│  HR console + chat  │
└─────────────────────┘
```

## Tech Stack

| Layer | Choice |
|---|---|
| Agent | Claude API (`claude-sonnet-4-6`) with native `tool_use` |
| Backend | Python + FastAPI (async) |
| Frontend | Vite + React + TypeScript + Tailwind |
| Database | Supabase PostgreSQL + pgvector |
| Embeddings | OpenAI `text-embedding-3-small` (1536d) |
| ORM | SQLAlchemy (async) |

## Frontend

The UI is split into two surfaces with separate shells:

- **HR Console** (`/dashboard`, `/escalations`, `/audit`) — onboarding progress cards, the escalation review queue (resolve/reject), and the full agent audit log.
- **New Hire Chat** (`/employee`) — a policy Q&A chat with confidence badges and a "Connect with HR" link on escalated answers.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/onboarding/trigger` | Fire the onboarding agent for a new hire |
| `GET` | `/onboarding/{employee_id}` | Onboarding progress for one hire |
| `GET` | `/onboarding` | All active onboardings |
| `POST` | `/chat` | Run policy Q&A for `{question, employee_id}` |
| `GET` | `/escalations` | Open escalation queue |
| `PATCH` | `/escalations/{id}` | Resolve or reject an escalation |
| `GET` | `/audit-log` | Paginated agent action history |
| `GET` | `/health` | Liveness + DB check |
