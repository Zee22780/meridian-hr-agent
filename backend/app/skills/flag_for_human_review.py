from datetime import datetime, timezone

from app.db.supabase import async_session
from app.db.tables import Escalation
from app.skills.base import ClaudeSkill


class FlagForHumanReviewSkill(ClaudeSkill):
    name = "flag_for_human_review"
    description = (
        "Escalate an issue to the HR team for human review. Use this when a compliance "
        "item requires human action (I9 verification always escalates), when confidence "
        "is too low to answer a policy question, or when a tool fails and the workflow "
        "cannot continue automatically."
    )
    parameters = {
        "employee_db_id": {
            "type": "string",
            "description": "The UUID primary key of the employee in the database",
        },
        "type": {
            "type": "string",
            "enum": ["i9_verification", "policy_unclear", "tool_failure", "compliance", "other"],
            "description": "Category of the escalation",
        },
        "reason": {
            "type": "string",
            "description": "Plain-language explanation of why this needs human review",
        },
        "priority": {
            "type": "string",
            "enum": ["low", "medium", "high", "urgent"],
            "description": "Priority level — use 'urgent' for I9 and compliance items",
        },
        "context": {
            "type": "object",
            "description": "Optional structured context (e.g. which step failed, confidence score)",
            "optional": True,
        },
    }

    async def execute(
        self,
        employee_db_id: str,
        type: str,
        reason: str,
        priority: str,
        context: dict | None = None,
    ) -> dict:
        timestamp = datetime.now(timezone.utc).isoformat()

        async with async_session() as session:
            async with session.begin():
                escalation = Escalation(
                    employee_id=employee_db_id,
                    type=type,
                    severity=priority,
                    reason=reason,
                    context=context or {},
                    status="pending",
                )
                session.add(escalation)
                await session.flush()
                escalation_id = str(escalation.id)

        # Mock HR notification — swap for real email/Slack post-MVP
        print(
            f"[flag_for_human_review] ESCALATION {escalation_id} | "
            f"type={type!r} priority={priority!r} | {reason}"
        )

        return {
            "status": "escalated",
            "escalation_id": escalation_id,
            "type": type,
            "priority": priority,
            "timestamp": timestamp,
        }
