"""
Phase 4, Task 2 smoke test — verify the agentic loop runs end-to-end.

Usage:
    cd /path/to/meridian-hr-agent
    python scripts/test_agent_loop.py
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "backend" / ".env")
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.agent.orchestrator import OnboardingAgent


async def test_policy_qa():
    print("\n=== Test: Policy Q&A ===")
    agent = OnboardingAgent()
    result = await agent.run_policy_qa(
        question="What is the PTO policy?",
        employee_id="EMP001",
    )

    print(f"stop_reason : {result['stop_reason']}")
    print(f"tool_calls  : {len(result['tool_calls'])}")
    for tc in result["tool_calls"]:
        status = "ERROR" if tc["is_error"] else "ok"
        print(f"  [{status}] {tc['tool_name']} → {list(tc['output'].keys())}")
    print(f"response    : {result['response'][:300]}{'...' if len(result['response']) > 300 else ''}")

    assert result["stop_reason"] == "end_turn", f"Expected end_turn, got {result['stop_reason']}"
    assert any(tc["tool_name"] == "retrieve_policy" for tc in result["tool_calls"]), \
        "Expected retrieve_policy to be called"
    assert result["response"], "Expected non-empty response"
    print("PASSED")


async def test_onboarding_stub():
    print("\n=== Test: Onboarding stub (loop mechanics) ===")
    agent = OnboardingAgent()

    employee_data = {
        "employee_id": "EMP001",
        "first_name": "Alex",
        "last_name": "Rivera",
        "email": "alex.rivera@meridian.com",
        "start_date": "2025-02-03",
        "department": "Engineering",
        "title": "Software Engineer",
    }

    result = await agent.run_onboarding(employee_data)

    print(f"stop_reason : {result['stop_reason']}")
    print(f"tool_calls  : {len(result['tool_calls'])}")
    for tc in result["tool_calls"]:
        status = "ERROR" if tc["is_error"] else "ok"
        print(f"  [{status}] {tc['tool_name']}")
    print(f"response    : {result['response'][:300]}{'...' if len(result['response']) > 300 else ''}")

    assert result["stop_reason"] in ("end_turn", "max_turns"), \
        f"Unexpected stop_reason: {result['stop_reason']}"
    print("PASSED")


async def main():
    await test_policy_qa()
    await test_onboarding_stub()
    print("\nAll tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
