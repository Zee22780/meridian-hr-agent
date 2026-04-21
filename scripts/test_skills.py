"""
Phase 3 smoke test — exercise each skill in isolation with sample inputs.

Usage:
    cd /path/to/meridian-hr-agent
    python scripts/test_skills.py
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "backend" / ".env")
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import json


def _section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


async def test_send_email() -> None:
    _section("send_email")
    from app.skills.send_email import SendEmailSkill
    skill = SendEmailSkill()
    result = await skill.execute(
        recipient="jane.doe@meridian.com",
        subject="Welcome to Meridian!",
        body="Hi Jane, welcome aboard. We're excited to have you.",
        attachments=["employee_handbook.pdf", "benefits_guide.pdf"],
    )
    print(json.dumps(result, indent=2))
    assert result["status"] == "sent"
    print("PASS")


async def test_schedule_meeting() -> None:
    _section("schedule_meeting")
    from app.skills.schedule_meeting import ScheduleMeetingSkill
    skill = ScheduleMeetingSkill()
    result = await skill.execute(
        contact_id="EMP006",
        new_hire_email="jane.doe@meridian.com",
        new_hire_start_date="2026-05-01",
        title="Onboarding: Meet Marketing",
    )
    print(json.dumps(result, indent=2))
    assert result["status"] == "scheduled"
    print("PASS")


async def test_lookup_employee() -> None:
    _section("lookup_employee")
    from app.skills.lookup_employee import LookupEmployeeSkill
    skill = LookupEmployeeSkill()

    result = await skill.execute(employee_id="EMP001")
    print(json.dumps(result, indent=2))
    assert result["status"] == "found"

    result_missing = await skill.execute(employee_id="EMP999")
    print(json.dumps(result_missing, indent=2))
    assert result_missing["status"] == "not_found"
    print("PASS")


async def test_retrieve_policy() -> None:
    _section("retrieve_policy")
    from app.skills.retrieve_policy import RetrievePolicySkill
    skill = RetrievePolicySkill()
    result = await skill.execute(query="When does health insurance start for new employees?")
    print(json.dumps({**result, "documents": [
        {k: v for k, v in d.items() if k != "content"} for d in result["documents"]
    ]}, indent=2))
    assert "documents" in result
    assert "confidence_score" in result
    print("PASS")


async def test_registry() -> None:
    _section("registry / tool schemas")
    from app.skills.registry import build_registry, get_tool_schemas
    registry = build_registry()
    schemas = get_tool_schemas(registry)
    print(f"Skills registered: {list(registry.keys())}")
    print(f"Schema count: {len(schemas)}")
    for s in schemas:
        print(f"  - {s['name']}: {len(s['input_schema']['properties'])} params")
    assert len(schemas) == 6
    print("PASS")


async def main() -> None:
    print("Meridian HR Agent — Phase 3 Skills Smoke Test")

    await test_send_email()
    await test_schedule_meeting()
    await test_lookup_employee()
    await test_retrieve_policy()
    await test_registry()

    print("\n" + "=" * 60)
    print("  All smoke tests passed.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
