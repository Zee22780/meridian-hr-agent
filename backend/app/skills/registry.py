from app.skills.flag_for_human_review import FlagForHumanReviewSkill
from app.skills.lookup_employee import LookupEmployeeSkill
from app.skills.retrieve_policy import RetrievePolicySkill
from app.skills.schedule_meeting import ScheduleMeetingSkill
from app.skills.send_email import SendEmailSkill
from app.skills.update_onboarding_progress import UpdateOnboardingProgressSkill
from app.skills.base import ClaudeSkill


def build_registry() -> dict[str, ClaudeSkill]:
    """Instantiate all skills and return a name-keyed dict."""
    skills: list[ClaudeSkill] = [
        SendEmailSkill(),
        ScheduleMeetingSkill(),
        LookupEmployeeSkill(),
        UpdateOnboardingProgressSkill(),
        FlagForHumanReviewSkill(),
        RetrievePolicySkill(),
    ]
    return {skill.name: skill for skill in skills}


def get_tool_schemas(registry: dict[str, ClaudeSkill]) -> list[dict]:
    """Return the list of tool schemas to pass to the Claude API `tools` parameter."""
    return [skill.get_tool_schema() for skill in registry.values()]
