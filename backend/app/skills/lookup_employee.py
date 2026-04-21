from app.data.service import DataService
from app.skills.base import ClaudeSkill

_data = DataService()

# Fields that are safe to expose to the agent — never salary, SSN, or payroll data
_SAFE_FIELDS = {
    "employee_id", "first_name", "last_name", "email", "department",
    "title", "start_date", "manager_id", "manager_email",
    "employment_type", "location", "benefits_tier",
}


class LookupEmployeeSkill(ClaudeSkill):
    name = "lookup_employee"
    description = (
        "Look up an employee's profile from the HRIS by employee ID. "
        "Returns safe fields only (no salary, SSN, or payroll data)."
    )
    parameters = {
        "employee_id": {
            "type": "string",
            "description": "The employee ID to look up (e.g. 'EMP001')",
        },
        "fields": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional subset of fields to return",
            "optional": True,
        },
    }

    async def execute(
        self,
        employee_id: str,
        fields: list[str] | None = None,
    ) -> dict:
        employee = _data.get_employee(employee_id)
        if not employee:
            return {"status": "not_found", "employee_id": employee_id}

        # Filter to safe fields, then optionally narrow to requested fields
        safe = {k: v for k, v in employee.items() if k in _SAFE_FIELDS}
        if fields:
            requested = set(fields) & _SAFE_FIELDS
            safe = {k: v for k, v in safe.items() if k in requested}

        return {"status": "found", "employee": safe}
