from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.services.store import prompt_store

router = APIRouter(prefix="/internal/prompts", tags=["internal-prompts"])


class PushPayload(BaseModel):
    prompt_key: str = Field(min_length=1)
    version: int = Field(ge=1)
    checksum: str = Field(min_length=1)
    content: str = Field(min_length=1)
    variables_schema: dict[str, Any] | None = None
    published_at: str | None = None


@router.post("/push")
def push_prompt(
    payload: PushPayload,
    authorization: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization")
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Missing Idempotency-Key")

    if idempotency_key in prompt_store.idempotency_seen:
        return {
            "ok": True,
            "prompt_key": payload.prompt_key,
            "version": payload.version,
            "applied": False,
            "cache_state": "already_processed",
        }

    current = prompt_store.cache.get(payload.prompt_key)
    if current and current.checksum == payload.checksum:
        prompt_store.idempotency_seen.add(idempotency_key)
        return {
            "ok": True,
            "prompt_key": payload.prompt_key,
            "version": payload.version,
            "applied": False,
            "cache_state": "already_up_to_date",
        }

    prompt_store.upsert(
        prompt_key=payload.prompt_key,
        version=payload.version,
        checksum=payload.checksum,
        content=payload.content,
        variables_schema=payload.variables_schema,
    )
    prompt_store.idempotency_seen.add(idempotency_key)
    return {
        "ok": True,
        "prompt_key": payload.prompt_key,
        "version": payload.version,
        "applied": True,
        "cache_state": "updated",
    }


@router.get("/cache")
def read_cache() -> dict[str, Any]:
    return {
        "items": [
            {
                "prompt_key": item.prompt_key,
                "version": item.version,
                "checksum": item.checksum,
                "updated_at": item.updated_at.isoformat(),
            }
            for item in prompt_store.cache.values()
        ]
    }
