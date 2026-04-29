from fastapi import APIRouter, HTTPException

from app.agent.orchestrator import OnboardingAgent
from app.api.schemas import ChatRequest, ChatResponse
from app.data.service import DataService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    if not DataService().get_employee(payload.employee_id):
        raise HTTPException(
            status_code=404,
            detail=f"Employee '{payload.employee_id}' not found in HRIS.",
        )

    agent = OnboardingAgent()
    try:
        result = await agent.run_policy_qa(payload.question, payload.employee_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(
        answer=result.get("response", ""),
        confidence_score=result.get("confidence_score"),
        escalated=result.get("escalated", False),
        tool_calls=result.get("tool_calls", []),
    )
