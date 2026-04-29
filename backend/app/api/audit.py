from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import AuditLogEntry, AuditLogResponse
from app.db.supabase import get_db
from app.db.tables import AgentAction

router = APIRouter(prefix="/audit-log", tags=["audit"])


@router.get("", response_model=AuditLogResponse)
async def get_audit_log(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    action_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    base_query = select(AgentAction)
    count_query = select(func.count()).select_from(AgentAction)

    if action_type:
        base_query = base_query.where(AgentAction.action_type == action_type)
        count_query = count_query.where(AgentAction.action_type == action_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        base_query.order_by(AgentAction.timestamp.desc()).offset(offset).limit(page_size)
    )
    actions = result.scalars().all()

    return AuditLogResponse(
        items=[
            AuditLogEntry(
                id=a.id,
                agent_name=a.agent_name,
                action_type=a.action_type,
                employee_id=a.employee_id,
                input=a.input,
                output=a.output,
                timestamp=a.timestamp,
                status=a.status,
                error=a.error,
            )
            for a in actions
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
