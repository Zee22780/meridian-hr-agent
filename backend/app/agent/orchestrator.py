from app.skills.registry import build_registry, get_tool_schemas


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

    async def run_onboarding(self, employee_data: dict) -> dict:
        """
        Execute the autonomous onboarding workflow for a new hire.

        employee_data: dict matching the mock HRIS employee record shape
                       (employee_id, first_name, last_name, email, start_date, etc.)

        Returns a summary dict with workflow outcome and any escalations created.
        """
        raise NotImplementedError("Implemented in Phase 4, task 2 (agentic loop)")

    async def run_policy_qa(self, question: str, employee_id: str) -> dict:
        """
        Answer a policy question from a new hire.

        Returns either a sourced answer or an escalation record if confidence
        is below threshold or the question cannot be answered from policy docs.
        """
        raise NotImplementedError("Implemented in Phase 4, task 4 (policy Q&A workflow)")
