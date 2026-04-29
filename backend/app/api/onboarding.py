import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.orchestrator import OnboardingAgent
from app.api.schemas import (
    OnboardingProgressResponse,
    TriggerOnboardingRequest,
    TriggerOnboardingResponse,
)
from app.db.supabase import get_db
from app.db.tables import Employee, OnboardingProgress

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


async def _run_onboarding(employee_data: dict) -> None:
    agent = OnboardingAgent()
    try:
        await agent.run_onboarding(employee_data)
    except Exception as e:
        print(f"[onboarding] ERROR: workflow failed for {employee_data.get('email')}: {e}")


@router.post("/trigger", response_model=TriggerOnboardingResponse, status_code=202)
async def trigger_onboarding(
    payload: TriggerOnboardingRequest,
    background_tasks: BackgroundTasks,
):
    employee_data = payload.model_dump()
    background_tasks.add_task(_run_onboarding, employee_data)
    return TriggerOnboardingResponse(
        status="started",
        employee_id=payload.employee_id,
        message=f"Onboarding workflow started for {payload.first_name} {payload.last_name}.",
    )


@router.get("", response_model=list[OnboardingProgressResponse])
async def list_onboardings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Employee, OnboardingProgress)
        .outerjoin(OnboardingProgress, OnboardingProgress.employee_id == Employee.id)
        .order_by(Employee.created_at.desc())
    )
    rows = result.all()

    items = []
    for emp, prog in rows:
        items.append(OnboardingProgressResponse(
            employee_id=emp.id,
            employee_name=f"{emp.first_name} {emp.last_name}",
            email=emp.email,
            department=emp.department,
            title=emp.title,
            hire_date=emp.hire_date,
            onboarding_status=prog.status if prog else None,
            steps=prog.steps if prog else {},
            last_updated=prog.last_updated if prog else None,
        ))
    return items


@router.get("/{employee_id}", response_model=OnboardingProgressResponse)
async def get_onboarding(employee_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Employee, OnboardingProgress)
        .outerjoin(OnboardingProgress, OnboardingProgress.employee_id == Employee.id)
        .where(Employee.email == employee_id)
    )
    row = result.first()

    if row is None:
        # also try by UUID
        try:
            import uuid
            uid = uuid.UUID(employee_id)
            result2 = await db.execute(
                select(Employee, OnboardingProgress)
                .outerjoin(OnboardingProgress, OnboardingProgress.employee_id == Employee.id)
                .where(Employee.id == uid)
            )
            row = result2.first()
        except ValueError:
            pass

    if row is None:
        raise HTTPException(status_code=404, detail=f"Employee '{employee_id}' not found.")

    emp, prog = row
    return OnboardingProgressResponse(
        employee_id=emp.id,
        employee_name=f"{emp.first_name} {emp.last_name}",
        email=emp.email,
        department=emp.department,
        title=emp.title,
        hire_date=emp.hire_date,
        onboarding_status=prog.status if prog else None,
        steps=prog.steps if prog else {},
        last_updated=prog.last_updated if prog else None,
    )
