from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.entities import AgentIdempotencyKey
from app.schemas.internal_push import PushApplyResponse, PushPayload
from app.services.agent_store import prompt_store

router = APIRouter(prefix="/internal/prompts", tags=["agent-internal"])


def _validate_auth(authorization: str | None) -> None:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    expected = f"Bearer {settings.push_auth_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid bearer token")


@router.post("/push", response_model=PushApplyResponse)
def push_prompt(
    payload: PushPayload,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> PushApplyResponse:
    _validate_auth(authorization)
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Missing Idempotency-Key header")

    row = AgentIdempotencyKey(idempotency_key=idempotency_key)
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return PushApplyResponse(
            ok=True,
            prompt_key=payload.prompt_key,
            version=payload.version,
            applied=False,
            cache_state="already_processed",
        )

    current = prompt_store.get(payload.prompt_key)
    if current and current.checksum == payload.checksum:
        return PushApplyResponse(
            ok=True,
            prompt_key=payload.prompt_key,
            version=payload.version,
            applied=False,
            cache_state="already_up_to_date",
        )

    prompt_store.upsert(
        prompt_key=payload.prompt_key,
        version=payload.version,
        checksum=payload.checksum,
        content=payload.content,
        variables_schema=payload.variables_schema,
    )
    return PushApplyResponse(
        ok=True,
        prompt_key=payload.prompt_key,
        version=payload.version,
        applied=True,
        cache_state="updated",
    )


@router.get("/cache")
def read_cache() -> dict:
    return {
        "items": [
            {
                "prompt_key": row.prompt_key,
                "version": row.version,
                "checksum": row.checksum,
                "updated_at": row.updated_at.isoformat(),
            }
            for row in prompt_store.cache.values()
        ]
    }
