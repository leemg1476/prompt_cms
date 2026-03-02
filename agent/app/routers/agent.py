from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.graph import agent_graph
from app.services.store import prompt_store

router = APIRouter(prefix="/api/agent", tags=["agent"])


class AgentRunRequest(BaseModel):
    prompt_key: str = Field(min_length=1)
    user_input: str = Field(min_length=1)
    trace_name: str | None = None
    trace_tags: list[str] | None = None
    trace_metadata: dict[str, Any] | None = None


@router.post("/run")
def run_agent(body: AgentRunRequest) -> dict:
    if body.prompt_key not in prompt_store.cache:
        raise HTTPException(status_code=404, detail="Prompt not found in cache. Push prompt first.")

    invoke_config: dict[str, Any] = {}
    if body.trace_name:
        invoke_config["run_name"] = body.trace_name
    if body.trace_tags:
        invoke_config["tags"] = body.trace_tags
    if body.trace_metadata:
        invoke_config["metadata"] = body.trace_metadata

    result = agent_graph.invoke(
        {
            "prompt_key": body.prompt_key,
            "user_input": body.user_input,
            "output": "",
        },
        config=invoke_config or None,
    )
    return {
        "ok": True,
        "prompt_key": body.prompt_key,
        "output": result["output"],
        "tracing_enabled": settings.langsmith_tracing or settings.langchain_tracing_v2,
    }
