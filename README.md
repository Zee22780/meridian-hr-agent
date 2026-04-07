# Meridian HR Agent

An autonomous AI agent that handles new hire onboarding administrative tasks for Meridian's HR department. Built with Claude API, FastAPI, Supabase, and React.

## Overview

The agent operates across two workflows:

**Autonomous Onboarding** — When a new hire is created, the agent sends a welcome email, schedules onboarding meetings, delivers paperwork, and escalates compliance items (like I9 verification) to HR for human review.

**Policy Q&A** — New hires ask plain-language questions about company policies and the agent retrieves answers from the handbook using RAG with confidence scoring. Low-confidence or sensitive answers escalate to HR instead of guessing.

## Design Approach

The agent is built on composable Claude Skills — small, isolated modules (send email, schedule meeting, retrieve policy) with clear input/output contracts that combine into powerful workflows. Complex capabilities emerge from simple, well-designed primitives.

## Tech Stack

- **Agent:** Claude API with native `tool_use`
- **Backend:** Python + FastAPI
- **Frontend:** Vite + React + TypeScript
- **Database:** Supabase PostgreSQL + pgvector
- **Observability:** Structured audit logging to Supabase

## Getting Started

Setup instructions coming soon.
