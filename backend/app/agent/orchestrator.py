import json
import uuid
from datetime import datetime

import anthropic
from sqlalchemy import select

from app.data.service import DataService
from app.db.supabase import async_session
from app.db.tables import AgentAction, Employee
from app.skills.registry import build_registry, get_tool_schemas

_DEPT_HEAD_CONTACTS = {
    "Finance": "EMP007",
    "Design": "EMP008",
}


class OnboardingAgent:
    """
    Drives both HR agent workflows:
      - run_onboarding: autonomous new hire onboarding sequence
      - run_policy_qa: policy question answering with escalation

    Designed to be LangChain-compatible post-MVP — each ClaudeSkill maps
    directly to a LangChain Tool with no interface changes needed.
    """

    def __init__(self):
        self.registry = build_registry()
        self.tools = get_tool_schemas(self.registry)
        self.client = anthropic.AsyncAnthropic()

    async def _log_action(
        self,
        action_type: str,
        input: dict,
        output: dict,
        is_error: bool,
        employee_db_id: str | None = None,
    ) -> None:
        try:
            async with async_session() as session:
                async with session.begin():
                    session.add(AgentAction(
                        agent_name="OnboardingAgent",
                        action_type=action_type,
                        employee_id=uuid.UUID(employee_db_id) if employee_db_id else None,
                        input=input,
                        output=output,
                        status="error" if is_error else "success",
                        error=output.get("error") if is_error else None,
                    ))
        except Exception as e:
            print(f"[audit] WARNING: failed to log action {action_type}: {e}")

    async def _run_loop(
        self,
        messages: list[dict],
        system_prompt: str,
        max_turns: int = 10,
        employee_db_id: str | None = None,
    ) -> dict:
        """
        Core agentic loop shared by both workflows.

        Sends messages to Claude with tool definitions, dispatches tool_use blocks
        to the skill registry, feeds results back as tool_result messages, and
        repeats until stop_reason is end_turn or max_turns is exceeded.

        Returns: {response: str, tool_calls: list[dict], stop_reason: str}
        """
        tool_calls = []

        for _ in range(max_turns):
            response = await self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=system_prompt,
                tools=self.tools,
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                text = next(
                    (block.text for block in response.content if block.type == "text"),
                    "",
                )
                return {"response": text, "tool_calls": tool_calls, "stop_reason": "end_turn"}

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    skill = self.registry.get(block.name)
                    if skill is None:
                        result = {"error": f"Unknown tool: {block.name}"}
                        is_error = True
                    else:
                        try:
                            result = await skill.execute(**block.input)
                            is_error = False
                        except Exception as e:
                            result = {"error": str(e)}
                            is_error = True

                    tool_calls.append({
                        "tool_name": block.name,
                        "input": block.input,
                        "output": result,
                        "is_error": is_error,
                    })
                    await self._log_action(
                        action_type=block.name,
                        input=block.input,
                        output=result,
                        is_error=is_error,
                        employee_db_id=employee_db_id,
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                        "is_error": is_error,
                    })

                messages.append({"role": "user", "content": tool_results})
            else:
                break

        return {"response": "", "tool_calls": tool_calls, "stop_reason": "max_turns"}

    async def _upsert_employee(self, employee_data: dict) -> str:
        """Find or create the Employee DB record; return UUID string."""
        async with async_session() as session:
            async with session.begin():
                result = await session.execute(
                    select(Employee).where(Employee.email == employee_data["email"])
                )
                emp = result.scalar_one_or_none()
                if emp is None:
                    emp = Employee(
                        first_name=employee_data.get("first_name", ""),
                        last_name=employee_data.get("last_name", ""),
                        email=employee_data["email"],
                        department=employee_data.get("department"),
                        title=employee_data.get("title"),
                        hire_date=datetime.fromisoformat(employee_data["start_date"])
                                  if "start_date" in employee_data else None,
                        manager_id=employee_data.get("manager_id"),
                        manager_email=employee_data.get("manager_email"),
                        employment_type=employee_data.get("employment_type"),
                        location=employee_data.get("location"),
                    )
                    session.add(emp)
                    await session.flush()
                return str(emp.id)

    async def run_onboarding(self, employee_data: dict) -> dict:
        """
        Execute the autonomous onboarding workflow for a new hire.

        employee_data: dict matching the mock HRIS employee record shape
                       (employee_id, first_name, last_name, email, start_date, etc.)

        Returns a summary dict with workflow outcome and any escalations created.
        """
        employee_db_id = await self._upsert_employee(employee_data)

        manager_id = employee_data.get("manager_id", "EMP005")
        department = employee_data.get("department", "")
        dept_head_id = _DEPT_HEAD_CONTACTS.get(department, manager_id)
        first_name = employee_data.get("first_name", "")

        system = f"""You are an autonomous HR onboarding agent for Meridian. Execute the \
following workflow for the new hire. Complete ALL steps in order without asking for \
confirmation.

EMPLOYEE DB ID (use this for every update_onboarding_progress and flag_for_human_review call):
{employee_db_id}

WORKFLOW:

STEP 1 — WELCOME EMAIL
Call send_email:
  recipient: new hire email
  subject: "Welcome to Meridian, {first_name}!"
  body: warm welcome message referencing their start_date and role
Then call update_onboarding_progress: step="welcome_email", status="completed"

STEP 2 — SCHEDULE 6 ONBOARDING MEETINGS
Schedule meetings with each contact below using schedule_meeting. After scheduling each \
meeting, immediately call update_onboarding_progress. Pass already_booked with each \
previously booked slot to avoid conflicts. If a scheduling call fails, record it as \
status="failed" and continue to the next contact.

Contacts (in order):
  {manager_id}   — "Onboarding: Meet Your Manager"
  EMP006         — "Onboarding: Meet the Marketing VP"
  {dept_head_id} — "Onboarding: Meet Your Department Head"
  EMP009         — "Onboarding: Meet the CEO"
  EMP011         — "Onboarding: IT Setup & Equipment"
  EMP010         — "Onboarding: HR Check-In"

Step names for update_onboarding_progress: "meeting_manager", "meeting_marketing", \
"meeting_dept_head", "meeting_ceo", "meeting_it", "meeting_hr"

STEP 3 — SEND PAPERWORK
Call send_email with subject "Your Onboarding Paperwork" and body listing the forms \
(W-4, direct deposit, benefits enrollment form) and a reminder to complete within 30 days.
Then call update_onboarding_progress: step="paperwork_sent", status="completed"

STEP 4 — I9 ESCALATION (MANDATORY — NO EXCEPTIONS)
ALWAYS call flag_for_human_review:
  type: "i9_verification"
  reason: "Federal I-9 employment eligibility verification requires HR review. Must be \
completed within 3 business days of start date."
  priority: "urgent"
Then call update_onboarding_progress: step="i9_escalated", status="escalated"

After all steps are complete, write a brief summary of what was accomplished."""

        messages = [{"role": "user", "content": json.dumps(employee_data)}]
        result = await self._run_loop(messages, system, max_turns=20, employee_db_id=employee_db_id)

        enforced = await self._ensure_i9_escalated(employee_db_id, result["tool_calls"])
        if enforced is not None:
            await self._log_action(
                action_type="flag_for_human_review",
                input={"type": "i9_verification", "priority": "urgent"},
                output=enforced,
                is_error=False,
                employee_db_id=employee_db_id,
            )
            result["tool_calls"].append({
                "tool_name": "flag_for_human_review",
                "input": {"type": "i9_verification", "priority": "urgent"},
                "output": enforced,
                "is_error": False,
            })

        return result

    @staticmethod
    def _is_i9_related(question: str) -> bool:
        q = question.lower()
        return any(kw in q for kw in (
            "i-9", "i9", "i 9", "form i-9",
            "employment eligibility", "work authorization",
            "everify", "e-verify", "uscis",
        ))

    async def _ensure_i9_escalated(
        self, employee_db_id: str, tool_calls: list[dict]
    ) -> dict | None:
        """
        Hard-rule enforcement: if no successful i9_verification escalation exists
        in tool_calls, fire the skill directly and return the result.
        """
        already_escalated = any(
            not tc["is_error"]
            and tc["tool_name"] == "flag_for_human_review"
            and tc["output"].get("type") == "i9_verification"
            for tc in tool_calls
        )
        if already_escalated:
            return None

        skill = self.registry["flag_for_human_review"]
        result = await skill.execute(
            employee_db_id=employee_db_id,
            type="i9_verification",
            reason=(
                "Federal I-9 employment eligibility verification requires HR review. "
                "Must be completed within 3 business days of start date. "
                "[Hard rule enforcement — fired programmatically.]"
            ),
            priority="urgent",
        )
        return result

    async def run_policy_qa(self, question: str, employee_id: str) -> dict:
        """
        Answer a policy question from a new hire.

        Returns either a sourced answer (high confidence) or an escalation record
        routed to HR (confidence_score < 0.7 / should_escalate: true).
        """
        hris_data = DataService().get_employee(employee_id)
        if hris_data is None:
            raise ValueError(f"Employee {employee_id} not found in HRIS")
        employee_db_id = await self._upsert_employee(hris_data)

        first_name = hris_data.get("first_name", "the employee")
        department = hris_data.get("department", "")

        system = f"""You are an HR policy assistant for Meridian. When an employee asks a \
policy question, follow these steps in order:

STEP 1 — RETRIEVE POLICY
Call retrieve_policy with the employee's question as `query`.

STEP 2 — EVALUATE CONFIDENCE
Check the `should_escalate` field in the result:

  If should_escalate is TRUE (confidence below threshold):
    - Call flag_for_human_review:
        employee_db_id: {employee_db_id}
        type: "policy_unclear"
        reason: "Policy question could not be answered with sufficient confidence. \
Question: <restate the question>. Confidence score: <score from retrieve_policy result>."
        priority: "medium"
        context: {{"question": "<question>", "confidence_score": <score>}}
    - Then respond to the employee: tell them their question has been routed to HR \
and they will receive a response within 1 business day. Be warm and reassuring.

  If should_escalate is FALSE (confidence at or above threshold):
    - Answer the employee's question directly, using ONLY information from the \
retrieved documents.
    - Reference the relevant policy document by name (e.g. "According to the PTO policy…").
    - Do not invent or infer information not explicitly stated in the documents.

EMPLOYEE CONTEXT:
- Name: {first_name}
- Department: {department}
- employee_db_id: {employee_db_id}

RULES:
- Always call retrieve_policy before answering or escalating.
- If should_escalate is true, always escalate. Do not attempt to answer instead.
- Never guess at policy details not present in the retrieved documents.
- I9 HARD RULE: If the question involves I9 verification, employment eligibility, or \
work authorization, ALWAYS call flag_for_human_review with type="i9_verification" and \
priority="urgent", regardless of the confidence score. Never answer I9 questions directly."""

        messages = [{"role": "user", "content": question}]
        result = await self._run_loop(messages, system, employee_db_id=employee_db_id)

        if self._is_i9_related(question):
            enforced = await self._ensure_i9_escalated(employee_db_id, result["tool_calls"])
            if enforced is not None:
                await self._log_action(
                    action_type="flag_for_human_review",
                    input={"type": "i9_verification", "priority": "urgent"},
                    output=enforced,
                    is_error=False,
                    employee_db_id=employee_db_id,
                )
                result["tool_calls"].append({
                    "tool_name": "flag_for_human_review",
                    "input": {"type": "i9_verification", "priority": "urgent"},
                    "output": enforced,
                    "is_error": False,
                })

        return result
