import uuid
from datetime import datetime, timezone

from app.skills.base import ClaudeSkill


class SendEmailSkill(ClaudeSkill):
    name = "send_email"
    description = (
        "Compose and send an email to an employee or HR contact. "
        "Use this for welcome emails, paperwork requests, or any direct communication."
    )
    parameters = {
        "recipient": {"type": "string", "description": "Recipient email address"},
        "subject": {"type": "string", "description": "Email subject line"},
        "body": {"type": "string", "description": "Email body (plain text)"},
        "attachments": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional list of document names to attach",
            "optional": True,
        },
    }

    async def execute(
        self,
        recipient: str,
        subject: str,
        body: str,
        attachments: list[str] | None = None,
    ) -> dict:
        email_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Mock delivery — log to stdout; swap for real provider post-MVP
        print(f"[send_email] → {recipient} | subject: {subject!r}")
        if attachments:
            print(f"[send_email]   attachments: {attachments}")

        return {
            "status": "sent",
            "email_id": email_id,
            "recipient": recipient,
            "subject": subject,
            "timestamp": timestamp,
        }
