"""
Phase 4, Task 3 smoke test — verify the autonomous onboarding workflow end-to-end.

Usage:
    cd /path/to/meridian-hr-agent
    python scripts/test_onboarding_workflow.py
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "backend" / ".env")
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.agent.orchestrator import OnboardingAgent


EMPLOYEE = {
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


async def test_onboarding_workflow():
    print("\n=== Test: Autonomous Onboarding Workflow ===")
    agent = OnboardingAgent()
    result = await agent.run_onboarding(EMPLOYEE)

    tool_calls = result["tool_calls"]

    print(f"\nstop_reason : {result['stop_reason']}")
    print(f"tool_calls  : {len(tool_calls)}")
    print()
    print(f"{'#':<3} {'Tool':<32} {'Status':<8} {'Key Output'}")
    print("-" * 80)
    for i, tc in enumerate(tool_calls, 1):
        status = "ERROR" if tc["is_error"] else "ok"
        out = tc["output"]
        if tc["tool_name"] == "send_email":
            detail = f"to={out.get('recipient','?')} subject={out.get('subject','?')[:30]!r}"
        elif tc["tool_name"] == "schedule_meeting":
            detail = f"status={out.get('status')} date={out.get('date')} contact={out.get('contact_id')}"
        elif tc["tool_name"] == "update_onboarding_progress":
            detail = f"step={out.get('step')!r} → {out.get('step_status')}"
        elif tc["tool_name"] == "flag_for_human_review":
            detail = f"type={out.get('type')!r} priority={out.get('priority')}"
        else:
            detail = str(out)[:60]
        print(f"{i:<3} {tc['tool_name']:<32} {status:<8} {detail}")

    print()
    print(f"response    : {result['response'][:400]}{'...' if len(result['response']) > 400 else ''}")

    # --- Assertions ---
    assert result["stop_reason"] == "end_turn", \
        f"Expected end_turn, got {result['stop_reason']}"

    by_tool = {}
    for tc in tool_calls:
        by_tool.setdefault(tc["tool_name"], []).append(tc)

    assert len(by_tool.get("send_email", [])) >= 2, \
        "Expected at least 2 send_email calls (welcome + paperwork)"

    assert len(by_tool.get("schedule_meeting", [])) >= 5, \
        f"Expected ≥5 schedule_meeting calls, got {len(by_tool.get('schedule_meeting', []))}"

    i9_flags = [
        tc for tc in by_tool.get("flag_for_human_review", [])
        if tc["output"].get("type") == "i9_verification"
    ]
    assert i9_flags, "Expected flag_for_human_review with type='i9_verification'"

    assert len(by_tool.get("update_onboarding_progress", [])) >= 7, \
        f"Expected ≥7 update_onboarding_progress calls, got {len(by_tool.get('update_onboarding_progress', []))}"

    errors = [tc for tc in tool_calls if tc["is_error"]]
    assert not errors, f"Unexpected tool errors: {[e['tool_name'] for e in errors]}"

    print("\nPASSED")


async def main():
    await test_onboarding_workflow()
    print("\nAll tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
