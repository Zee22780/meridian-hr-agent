from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.supabase import async_session
from app.db.tables import OnboardingProgress
from app.skills.base import ClaudeSkill


class UpdateOnboardingProgressSkill(ClaudeSkill):
    name = "update_onboarding_progress"
    description = (
        "Record the completion or failure of a specific onboarding step for a new hire. "
        "Call this after every action (email sent, meeting scheduled, etc.) to keep the "
        "progress record current."
    )
    parameters = {
        "employee_db_id": {
            "type": "string",
            "description": "The UUID primary key of the employee in the database",
        },
        "step": {
            "type": "string",
            "description": (
                "Name of the onboarding step, e.g. 'welcome_email', 'meeting_manager', "
                "'paperwork_sent', 'i9_escalated'"
            ),
        },
        "status": {
            "type": "string",
            "enum": ["completed", "failed", "escalated", "skipped"],
            "description": "Outcome of this step",
        },
        "details": {
            "type": "object",
            "description": "Optional structured details about the step outcome",
            "optional": True,
        },
    }

    async def execute(
        self,
        employee_db_id: str,
        step: str,
        status: str,
        details: dict | None = None,
    ) -> dict:
        timestamp = datetime.now(timezone.utc).isoformat()

        async with async_session() as session:
            async with session.begin():
                result = await session.execute(
                    select(OnboardingProgress).where(
                        OnboardingProgress.employee_id == employee_db_id
                    )
                )
                progress = result.scalar_one_or_none()

                if progress is None:
                    progress = OnboardingProgress(
                        employee_id=employee_db_id,
                        status="in_progress",
                        steps={},
                        escalations=[],
                    )
                    session.add(progress)

                steps = dict(progress.steps or {})
                steps[step] = {"status": status, "timestamp": timestamp, **(details or {})}
                progress.steps = steps

                # If any step is escalated, mark the overall record as escalated
                if status == "escalated" and progress.status == "in_progress":
                    progress.status = "escalated"

        print(f"[update_onboarding_progress] employee={employee_db_id} step={step!r} → {status}")

        return {
            "status": "updated",
            "employee_db_id": employee_db_id,
            "step": step,
            "step_status": status,
            "timestamp": timestamp,
        }
