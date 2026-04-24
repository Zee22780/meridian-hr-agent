"""
Phase 4, Task 5 smoke test — verify the I9 hard rule fires in both workflows.

Usage:
    cd /path/to/meridian-hr-agent
    python scripts/test_i9_hard_rule.py
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "backend" / ".env")
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.agent.orchestrator import OnboardingAgent


EMPLOYEE = {
    "employee_id": "EMP002",
    "first_name": "Marcus",
    "last_name": "Chen",
    "email": "marcus.chen@meridian.com",
    "department": "Marketing",
    "title": "Marketing Coordinator",
    "manager_id": "EMP006",
    "manager_email": "diana.walsh@meridian.com",
    "start_date": "2026-06-02",
    "employment_type": "full_time",
    "location": "Remote",
}


async def test_policy_qa_i9_always_escalates():
    print("\n=== Test: Policy Q&A — I9 question always escalates ===")
    agent = OnboardingAgent()
    result = await agent.run_policy_qa(
        question="What documents do I need to bring for my I9 verification?",
        employee_id="EMP001",
    )

    print(f"stop_reason : {result['stop_reason']}")
    print(f"tool_calls  : {len(result['tool_calls'])}")
    for tc in result["tool_calls"]:
        status = "ERROR" if tc["is_error"] else "ok"
        print(f"  [{status}] {tc['tool_name']} → {list(tc['output'].keys())}")
    print(f"response    : {result['response'][:300]}{'...' if len(result['response']) > 300 else ''}")

    assert result["stop_reason"] == "end_turn", f"Expected end_turn, got {result['stop_reason']}"

    i9_flags = [
        tc for tc in result["tool_calls"]
        if not tc["is_error"]
        and tc["tool_name"] == "flag_for_human_review"
        and tc["output"].get("type") == "i9_verification"
    ]
    assert i9_flags, "Expected flag_for_human_review with type='i9_verification'"
    assert i9_flags[0]["output"].get("priority") == "urgent", \
        f"Expected priority='urgent', got {i9_flags[0]['output'].get('priority')}"

    response_lower = result["response"].lower()
    answered_directly = (
        "you will need" in response_lower
        and "hr" not in response_lower
        and "routed" not in response_lower
        and "escalat" not in response_lower
    )
    assert not answered_directly, \
        "I9 question must be escalated to HR, not answered directly"

    print("PASSED")


async def test_onboarding_i9_enforcement():
    print("\n=== Test: Onboarding — I9 escalation always present ===")
    agent = OnboardingAgent()
    result = await agent.run_onboarding(EMPLOYEE)

    tool_calls = result["tool_calls"]
    print(f"stop_reason : {result['stop_reason']}")
    print(f"tool_calls  : {len(tool_calls)}")
    for tc in tool_calls:
        if tc["tool_name"] == "flag_for_human_review":
            status = "ERROR" if tc["is_error"] else "ok"
            print(f"  [{status}] {tc['tool_name']} type={tc['output'].get('type')} priority={tc['output'].get('priority')}")

    i9_flags = [
        tc for tc in tool_calls
        if not tc["is_error"]
        and tc["tool_name"] == "flag_for_human_review"
        and tc["output"].get("type") == "i9_verification"
    ]
    assert i9_flags, "Expected flag_for_human_review with type='i9_verification'"
    assert i9_flags[0]["output"].get("priority") == "urgent", \
        f"Expected priority='urgent', got {i9_flags[0]['output'].get('priority')}"

    print("PASSED")


async def main():
    await test_policy_qa_i9_always_escalates()
    await test_onboarding_i9_enforcement()
    print("\nAll tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
