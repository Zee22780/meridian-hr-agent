from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


# ── Onboarding ────────────────────────────────────────────────────────────────

class TriggerOnboardingRequest(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    email: str
    department: str | None = None
    title: str | None = None
    start_date: str  # ISO date string e.g. "2025-05-01"
    manager_id: str | None = None
    manager_email: str | None = None
    employment_type: str | None = None
    location: str | None = None


class TriggerOnboardingResponse(BaseModel):
    status: str  # "started"
    employee_id: str
    message: str


class OnboardingStepStatus(BaseModel):
    status: str
    timestamp: str | None = None
    meeting_time: str | None = None


class OnboardingProgressResponse(BaseModel):
    employee_id: UUID
    employee_name: str
    email: str
    department: str | None
    title: str | None
    hire_date: datetime | None
    onboarding_status: str | None
    steps: dict[str, Any]
    last_updated: datetime | None


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str
    employee_id: str  # HRIS ID e.g. "EMP001"


class ChatResponse(BaseModel):
    answer: str
    confidence_score: float | None
    escalated: bool
    tool_calls: list[dict[str, Any]]


# ── Escalations ───────────────────────────────────────────────────────────────

class EscalationResponse(BaseModel):
    id: UUID
    employee_id: UUID
    employee_name: str | None
    type: str
    severity: str
    reason: str
    context: dict[str, Any] | None
    assigned_to: str | None
    status: str
    created_at: datetime
    resolved_at: datetime | None
    resolution: str | None


class ResolveEscalationRequest(BaseModel):
    status: str  # "resolved" or "rejected"
    resolution: str | None = None
    assigned_to: str | None = None


class ResolveEscalationResponse(BaseModel):
    id: UUID
    status: str
    resolved_at: datetime | None
    resolution: str | None


# ── Audit Log ─────────────────────────────────────────────────────────────────

class AuditLogEntry(BaseModel):
    id: UUID
    agent_name: str
    action_type: str
    employee_id: UUID | None
    input: dict[str, Any] | None
    output: dict[str, Any] | None
    timestamp: datetime
    status: str
    error: str | None


class AuditLogResponse(BaseModel):
    items: list[AuditLogEntry]
    total: int
    page: int
    page_size: int
