from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.graph import agent_graph
from app.services.store import prompt_store

router = APIRouter(prefix="/api/agent", tags=["agent"])


class AgentRunRequest(BaseModel):
    prompt_key: str = Field(min_length=1)
    user_input: str = Field(min_length=1)


@router.post("/run")
def run_agent(body: AgentRunRequest) -> dict:
    if body.prompt_key not in prompt_store.cache:
        raise HTTPException(status_code=404, detail="Prompt not found in cache. Push prompt first.")

    result = agent_graph.invoke(
        {
            "prompt_key": body.prompt_key,
            "user_input": body.user_input,
            "output": "",
        }
    )
    return {
        "ok": True,
        "prompt_key": body.prompt_key,
        "output": result["output"],
    }
