from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import (
    AgentRegistry,
    Prompt,
    PromptActivePointer,
    PromptSubscription,
    PromptVersion,
    PublishEvent,
    PushDelivery,
)
from app.schemas.prompts import DraftCreateRequest, PublishResult
from app.services.hash_utils import compute_checksum


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _get_prompt_by_key(db: Session, prompt_key: str) -> Prompt | None:
    return db.scalar(select(Prompt).where(Prompt.prompt_key == prompt_key))


def create_draft(db: Session, prompt_key: str, body: DraftCreateRequest) -> dict:
    prompt = _get_prompt_by_key(db, prompt_key)
    if prompt is None:
        prompt = Prompt(
            prompt_key=prompt_key,
            description=body.description,
            owner_team=body.owner_team,
        )
        db.add(prompt)
        db.flush()
    else:
        if body.description is not None:
            prompt.description = body.description
        if body.owner_team is not None:
            prompt.owner_team = body.owner_team
        prompt.updated_at = utcnow()

    max_version = db.scalar(select(func.max(PromptVersion.version)).where(PromptVersion.prompt_id == prompt.id))
    next_version = (max_version or 0) + 1

    draft = PromptVersion(
        prompt_id=prompt.id,
        version=next_version,
        status="draft",
        content=body.content,
        variables_schema=body.variables_schema,
        checksum=compute_checksum(body.content),
        created_by=body.created_by,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return {"ok": True, "prompt_key": prompt_key, "version": draft.version, "status": draft.status}


def _ensure_active_pointer(db: Session, prompt_id: int, active_version_id: int) -> None:
    pointer = db.get(PromptActivePointer, prompt_id)
    if pointer is None:
        pointer = PromptActivePointer(prompt_id=prompt_id, active_version_id=active_version_id)
        db.add(pointer)
    else:
        pointer.active_version_id = active_version_id
        pointer.updated_at = utcnow()


def _build_deliveries(db: Session, publish_event_id: int, prompt_id: int, environment: str) -> int:
    agent_rows = list(
        db.execute(
            select(AgentRegistry)
            .join(PromptSubscription, PromptSubscription.agent_id == AgentRegistry.id)
            .where(
                PromptSubscription.prompt_id == prompt_id,
                AgentRegistry.environment == environment,
                AgentRegistry.is_enabled.is_(True),
            )
        ).scalars()
    )

    if not agent_rows:
        # Fallback for bootstrap mode: push to all enabled agents in the target environment.
        agent_rows = list(
            db.execute(
                select(AgentRegistry).where(
                    AgentRegistry.environment == environment,
                    AgentRegistry.is_enabled.is_(True),
                )
            ).scalars()
        )

    count = 0
    now = utcnow()
    for agent in agent_rows:
        delivery = PushDelivery(
            publish_event_id=publish_event_id,
            agent_id=agent.id,
            idempotency_key=f"{publish_event_id}-{agent.id}",
            attempt=0,
            status="pending",
            next_retry_at=now,
        )
        db.add(delivery)
        count += 1
    return count


def publish_prompt(db: Session, prompt_key: str, environment: str, published_by: str | None) -> PublishResult:
    prompt = _get_prompt_by_key(db, prompt_key)
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")

    latest_draft = db.scalar(
        select(PromptVersion)
        .where(PromptVersion.prompt_id == prompt.id, PromptVersion.status == "draft")
        .order_by(PromptVersion.version.desc())
    )
    if latest_draft is None:
        raise HTTPException(status_code=400, detail="No draft version to publish")

    current_active_versions = db.execute(
        select(PromptVersion).where(PromptVersion.prompt_id == prompt.id, PromptVersion.status == "active")
    ).scalars()
    for row in current_active_versions:
        row.status = "archived"
        row.updated_at = utcnow()

    latest_draft.status = "active"
    latest_draft.updated_at = utcnow()
    _ensure_active_pointer(db, prompt.id, latest_draft.id)

    event = PublishEvent(
        prompt_id=prompt.id,
        version_id=latest_draft.id,
        environment=environment,
        published_by=published_by,
    )
    db.add(event)
    db.flush()

    deliveries_created = _build_deliveries(db, event.id, prompt.id, environment)
    db.commit()

    return PublishResult(
        ok=True,
        prompt_key=prompt_key,
        publish_event_id=event.id,
        version=latest_draft.version,
        environment=environment,
        deliveries_created=deliveries_created,
    )


def rollback_prompt(
    db: Session,
    prompt_key: str,
    to_version: int,
    environment: str,
    published_by: str | None,
) -> PublishResult:
    prompt = _get_prompt_by_key(db, prompt_key)
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")

    target = db.scalar(
        select(PromptVersion).where(
            PromptVersion.prompt_id == prompt.id,
            PromptVersion.version == to_version,
        )
    )
    if target is None:
        raise HTTPException(status_code=404, detail="Target version not found")

    active_rows = db.execute(
        select(PromptVersion).where(PromptVersion.prompt_id == prompt.id, PromptVersion.status == "active")
    ).scalars()
    for row in active_rows:
        row.status = "archived"
        row.updated_at = utcnow()

    target.status = "active"
    target.updated_at = utcnow()
    _ensure_active_pointer(db, prompt.id, target.id)

    event = PublishEvent(
        prompt_id=prompt.id,
        version_id=target.id,
        environment=environment,
        published_by=published_by,
    )
    db.add(event)
    db.flush()

    deliveries_created = _build_deliveries(db, event.id, prompt.id, environment)
    db.commit()

    return PublishResult(
        ok=True,
        prompt_key=prompt_key,
        publish_event_id=event.id,
        version=target.version,
        environment=environment,
        deliveries_created=deliveries_created,
    )
