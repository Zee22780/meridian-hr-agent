import json

import anthropic

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
        self.client = anthropic.AsyncAnthropic()

    async def _run_loop(
        self,
        messages: list[dict],
        system_prompt: str,
        max_turns: int = 10,
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

    async def run_onboarding(self, employee_data: dict) -> dict:
        """
        Execute the autonomous onboarding workflow for a new hire.

        employee_data: dict matching the mock HRIS employee record shape
                       (employee_id, first_name, last_name, email, start_date, etc.)

        Returns a summary dict with workflow outcome and any escalations created.
        System prompt will be expanded in task 3.
        """
        system = (
            "You are an autonomous HR onboarding agent. "
            "Use the available tools to onboard the new hire described in the user message."
        )
        messages = [{"role": "user", "content": json.dumps(employee_data)}]
        return await self._run_loop(messages, system)

    async def run_policy_qa(self, question: str, employee_id: str) -> dict:
        """
        Answer a policy question from a new hire.

        Returns either a sourced answer or an escalation record if confidence
        is below threshold or the question cannot be answered from policy docs.
        System prompt will be expanded in task 4.
        """
        system = (
            "You are an HR policy assistant. "
            "Answer the employee's question using the retrieve_policy tool."
        )
        messages = [{"role": "user", "content": f"Employee {employee_id} asks: {question}"}]
        return await self._run_loop(messages, system)
