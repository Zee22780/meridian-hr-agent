import uuid
from datetime import date, datetime, timezone

from app.data.service import DataService
from app.skills.base import ClaudeSkill

_data = DataService()


class ScheduleMeetingSkill(ClaudeSkill):
    name = "schedule_meeting"
    description = (
        "Schedule a 1:1 onboarding meeting between the new hire and a specific contact. "
        "Checks the contact's mock calendar for the first available slot relative to the "
        "new hire's start date and returns the scheduled time. New hires are always available."
    )
    parameters = {
        "contact_id": {
            "type": "string",
            "description": "Employee ID of the contact to meet with (e.g. 'EMP006')",
        },
        "new_hire_email": {
            "type": "string",
            "description": "New hire's email address",
        },
        "new_hire_start_date": {
            "type": "string",
            "description": "New hire's start date in YYYY-MM-DD format",
        },
        "title": {
            "type": "string",
            "description": "Meeting title (e.g. 'Onboarding: Meet your Manager')",
        },
        "already_booked": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "time": {"type": "string"},
                },
            },
            "description": "Slots already scheduled for this new hire (to avoid conflicts)",
            "optional": True,
        },
    }

    async def execute(
        self,
        contact_id: str,
        new_hire_email: str,
        new_hire_start_date: str,
        title: str,
        already_booked: list[dict] | None = None,
    ) -> dict:
        start_date = date.fromisoformat(new_hire_start_date)
        booked = already_booked or []

        slot = _data.find_first_available_slot(contact_id, start_date, booked)
        if not slot:
            return {
                "status": "failed",
                "reason": f"No available slots found for contact {contact_id}",
            }

        meeting_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        print(
            f"[schedule_meeting] {title!r} | {new_hire_email} ↔ {slot['contact_email']} "
            f"| {slot['date']} {slot['time']}"
        )

        return {
            "status": "scheduled",
            "meeting_id": meeting_id,
            "title": title,
            "date": slot["date"],
            "time": slot["time"],
            "duration_minutes": slot["duration_minutes"],
            "contact_id": contact_id,
            "contact_name": slot["contact_name"],
            "contact_email": slot["contact_email"],
            "meeting_role": slot["meeting_role"],
            "attendees": [new_hire_email, slot["contact_email"]],
            "timestamp": timestamp,
        }
