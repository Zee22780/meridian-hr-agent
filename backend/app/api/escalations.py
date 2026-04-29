from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    EscalationResponse,
    ResolveEscalationRequest,
    ResolveEscalationResponse,
)
from app.db.supabase import get_db
from app.db.tables import Employee, Escalation

router = APIRouter(prefix="/escalations", tags=["escalations"])

_VALID_STATUSES = {"resolved", "rejected"}


def _to_response(esc: Escalation, emp: Employee | None) -> EscalationResponse:
    return EscalationResponse(
        id=esc.id,
        employee_id=esc.employee_id,
        employee_name=f"{emp.first_name} {emp.last_name}" if emp else None,
        type=esc.type,
        severity=esc.severity,
        reason=esc.reason,
        context=esc.context,
        assigned_to=esc.assigned_to,
        status=esc.status,
        created_at=esc.created_at,
        resolved_at=esc.resolved_at,
        resolution=esc.resolution,
    )


@router.get("", response_model=list[EscalationResponse])
async def list_escalations(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Escalation, Employee)
        .outerjoin(Employee, Employee.id == Escalation.employee_id)
        .order_by(Escalation.created_at.desc())
    )
    if status:
        query = query.where(Escalation.status == status)

    result = await db.execute(query)
    return [_to_response(esc, emp) for esc, emp in result.all()]


@router.patch("/{escalation_id}", response_model=ResolveEscalationResponse)
async def resolve_escalation(
    escalation_id: UUID,
    payload: ResolveEscalationRequest,
    db: AsyncSession = Depends(get_db),
):
    if payload.status not in _VALID_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"status must be one of: {', '.join(sorted(_VALID_STATUSES))}",
        )

    result = await db.execute(select(Escalation).where(Escalation.id == escalation_id))
    esc = result.scalar_one_or_none()
    if esc is None:
        raise HTTPException(status_code=404, detail="Escalation not found.")

    esc.status = payload.status
    esc.resolved_at = datetime.now(timezone.utc)
    if payload.resolution is not None:
        esc.resolution = payload.resolution
    if payload.assigned_to is not None:
        esc.assigned_to = payload.assigned_to

    await db.commit()
    await db.refresh(esc)

    return ResolveEscalationResponse(
        id=esc.id,
        status=esc.status,
        resolved_at=esc.resolved_at,
        resolution=esc.resolution,
    )
