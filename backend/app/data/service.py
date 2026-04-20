import json
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

_MOCK_DIR = Path(__file__).parent / "mock"


def _load_employees() -> list[dict]:
    with open(_MOCK_DIR / "employees.json") as f:
        return json.load(f)


def _load_calendar() -> dict:
    with open(_MOCK_DIR / "calendar.json") as f:
        return json.load(f)


class DataService:
    def __init__(self):
        self._employees: list[dict] = _load_employees()
        self._calendar: dict = _load_calendar()
        self._employee_index: dict[str, dict] = {
            e["employee_id"]: e for e in self._employees
        }

    # ── Employee methods ──────────────────────────────────────────────────────

    def get_employee(self, employee_id: str) -> Optional[dict]:
        """Return a single employee record by ID, or None if not found."""
        return self._employee_index.get(employee_id)

    def get_all_employees(self) -> list[dict]:
        """Return all employee records."""
        return list(self._employees)

    def get_employees_by_department(self, department: str) -> list[dict]:
        """Return all employees in the given department."""
        return [e for e in self._employees if e["department"] == department]

    def get_peers(self, employee_id: str) -> list[dict]:
        """Return same-department employees excluding the given employee_id."""
        employee = self.get_employee(employee_id)
        if not employee:
            return []
        return [
            e for e in self._employees
            if e["department"] == employee["department"]
            and e["employee_id"] != employee_id
        ]

    # ── Calendar methods ──────────────────────────────────────────────────────

    def get_contact(self, contact_id: str) -> Optional[dict]:
        """Return a calendar contact entry (without the _note key)."""
        entry = self._calendar.get(contact_id)
        if not entry or contact_id == "_note":
            return None
        return entry

    def get_all_contacts(self) -> dict[str, dict]:
        """Return all calendar contacts keyed by contact_id."""
        return {k: v for k, v in self._calendar.items() if k != "_note"}

    def get_available_slots(
        self, contact_id: str, start_date: date
    ) -> list[dict]:
        """
        Return slots for a contact with absolute dates resolved from start_date.
        Each returned slot: {date, time, duration_minutes, contact_id, contact_name}
        """
        contact = self.get_contact(contact_id)
        if not contact:
            return []
        slots = []
        for slot in contact["available_slots"]:
            meeting_date = start_date + timedelta(days=slot["day_offset"])
            slots.append({
                "date": meeting_date.isoformat(),
                "time": slot["time"],
                "duration_minutes": slot["duration_minutes"],
                "contact_id": contact_id,
                "contact_name": contact["name"],
                "contact_email": contact["email"],
                "meeting_role": contact["meeting_role"],
            })
        return slots

    def find_first_available_slot(
        self,
        contact_id: str,
        start_date: date,
        booked_slots: list[dict],
    ) -> Optional[dict]:
        """
        Return the first slot for contact_id that doesn't conflict with booked_slots.
        booked_slots: list of {date, time} dicts already scheduled.
        """
        booked_keys = {(s["date"], s["time"]) for s in booked_slots}
        for slot in self.get_available_slots(contact_id, start_date):
            if (slot["date"], slot["time"]) not in booked_keys:
                return slot
        return None
