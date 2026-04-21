from typing import Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.ai.agent import run_agent

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: Any


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Primary gateway — passes user input through the LangGraph agent."""
    try:
        result = run_agent(request.message)
        return ChatResponse(response=result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}"
        )
