"""
Phase 4, Task 7 & 8 — end-to-end workflow tests.

Covers three policy Q&A paths and the full onboarding workflow:
  1. High confidence  — clear on-topic question → answer, no escalation
  2. Low confidence   — off-topic question → escalation (hard-rule enforcement verified)
  3. I9 hard rule     — I9 question → urgent escalation regardless of confidence
  4. Onboarding       — full autonomous onboarding smoke test

Usage:
    cd /path/to/meridian-hr-agent
    python scripts/test_workflows.py
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "backend" / ".env")
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.agent.orchestrator import OnboardingAgent


EMPLOYEE_ID = "EMP001"

ONBOARDING_EMPLOYEE = {
    "employee_id": "EMP001",
    "first_name": "Jordan",
    "last_name": "Rivera",
    "email": "jordan.rivera@meridian.com",
    "department": "Engineering",
    "title": "Software Engineer II",
    "manager_id": "EMP005",
    "manager_email": "priya.nair@meridian.com",
    "start_date": "2026-05-05",
    "employment_type": "full_time",
    "location": "Remote",
}


def _print_result(result: dict) -> None:
    tool_calls = result["tool_calls"]
    print(f"  stop_reason      : {result['stop_reason']}")
    print(f"  tool_calls       : {len(tool_calls)}")
    print(f"  confidence_score : {result.get('confidence_score')}")
    print(f"  escalated        : {result.get('escalated')}")
    print()

    for i, tc in enumerate(tool_calls, 1):
        status = "ERROR" if tc["is_error"] else "ok"
        out = tc["output"]
        if tc["tool_name"] == "retrieve_policy":
            detail = (
                f"score={out.get('confidence_score')} "
                f"level={out.get('confidence_level')} "
                f"should_escalate={out.get('should_escalate')}"
            )
        elif tc["tool_name"] == "flag_for_human_review":
            detail = f"type={out.get('type')!r} priority={out.get('priority')}"
        else:
            detail = str(out)[:80]
        print(f"    [{i}] {tc['tool_name']:<32} {status:<6} {detail}")

    print()
    print(f"  response: {result['response'][:300]}{'...' if len(result['response']) > 300 else ''}")


async def test_high_confidence(agent: OnboardingAgent) -> None:
    print("\n=== Test 1: High Confidence Path ===")
    print("  question: How many PTO days do I get per year?\n")

    result = await agent.run_policy_qa(
        question="How many PTO days do I get per year?",
        employee_id=EMPLOYEE_ID,
    )
    _print_result(result)

    assert result["stop_reason"] == "end_turn", \
        f"Expected end_turn, got {result['stop_reason']}"
    assert result["confidence_score"] is not None, \
        "Expected confidence_score in result"
    assert not result["escalated"], \
        f"High-confidence question should NOT escalate — got escalated=True"

    retrieve_calls = [tc for tc in result["tool_calls"] if tc["tool_name"] == "retrieve_policy"]
    assert retrieve_calls, "Expected at least one retrieve_policy call"

    print("  PASSED")


async def test_low_confidence(agent: OnboardingAgent) -> None:
    print("\n=== Test 2: Low Confidence Path (escalation hard-rule) ===")
    question = "What is the company's policy on stock option vesting schedules?"
    print(f"  question: {question}\n")

    result = await agent.run_policy_qa(question=question, employee_id=EMPLOYEE_ID)
    _print_result(result)

    assert result["stop_reason"] == "end_turn", \
        f"Expected end_turn, got {result['stop_reason']}"
    assert result["escalated"], \
        "Low-confidence question MUST escalate — got escalated=False"

    escalations = [
        tc for tc in result["tool_calls"]
        if tc["tool_name"] == "flag_for_human_review" and not tc["is_error"]
    ]
    assert escalations, "Expected flag_for_human_review to be called"

    types = {tc["output"].get("type") for tc in escalations}
    assert "policy_unclear" in types, \
        f"Expected escalation type 'policy_unclear', got {types}"

    print("  PASSED")


async def test_i9_hard_rule(agent: OnboardingAgent) -> None:
    print("\n=== Test 3: I9 Hard Rule ===")
    question = "How do I complete my I-9 form?"
    print(f"  question: {question}\n")

    result = await agent.run_policy_qa(question=question, employee_id=EMPLOYEE_ID)
    _print_result(result)

    assert result["escalated"], \
        "I9 question MUST always escalate — got escalated=False"

    i9_escalations = [
        tc for tc in result["tool_calls"]
        if tc["tool_name"] == "flag_for_human_review"
        and not tc["is_error"]
        and tc["output"].get("type") == "i9_verification"
    ]
    assert i9_escalations, \
        "Expected flag_for_human_review with type='i9_verification'"
    assert i9_escalations[0]["output"].get("priority") == "urgent", \
        "I9 escalation must have priority='urgent'"

    print("  PASSED")


async def test_onboarding(agent: OnboardingAgent) -> None:
    print("\n=== Test 4: Autonomous Onboarding Workflow ===")
    result = await agent.run_onboarding(ONBOARDING_EMPLOYEE)

    tool_calls = result["tool_calls"]
    print(f"  stop_reason : {result['stop_reason']}")
    print(f"  tool_calls  : {len(tool_calls)}")
    print()

    by_tool: dict[str, list] = {}
    for tc in tool_calls:
        by_tool.setdefault(tc["tool_name"], []).append(tc)

    for name, calls in by_tool.items():
        ok = sum(1 for c in calls if not c["is_error"])
        err = len(calls) - ok
        print(f"    {name:<32} ok={ok}  err={err}")

    print(f"\n  response: {result['response'][:300]}{'...' if len(result['response']) > 300 else ''}")

    assert result["stop_reason"] == "end_turn", \
        f"Expected end_turn, got {result['stop_reason']}"
    assert len(by_tool.get("send_email", [])) >= 2, \
        "Expected ≥2 send_email calls"
    assert len(by_tool.get("schedule_meeting", [])) >= 5, \
        "Expected ≥5 schedule_meeting calls"

    i9_flags = [
        tc for tc in by_tool.get("flag_for_human_review", [])
        if tc["output"].get("type") == "i9_verification"
    ]
    assert i9_flags, "Expected i9_verification escalation"

    errors = [tc for tc in tool_calls if tc["is_error"]]
    assert not errors, f"Unexpected tool errors: {[e['tool_name'] for e in errors]}"

    print("\n  PASSED")


async def main() -> None:
    agent = OnboardingAgent()

    await test_high_confidence(agent)
    await test_low_confidence(agent)
    await test_i9_hard_rule(agent)
    await test_onboarding(agent)

    print("\n\nAll tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
