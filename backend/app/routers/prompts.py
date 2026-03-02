from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.entities import Prompt, PromptActivePointer, PromptVersion, PublishEvent, PushDelivery
from app.schemas.prompts import (
    DraftCreateRequest,
    PromptDetail,
    PromptSummary,
    PromptVersionItem,
    PublishEventItem,
    PublishRequest,
    PublishResult,
    PushDeliveryItem,
    RollbackRequest,
)
from app.services.publish_service import create_draft, publish_prompt, rollback_prompt
from app.services.worker_service import run_worker_once

router = APIRouter(prefix="/api", tags=["cms"])


@router.get("/prompts", response_model=list[PromptSummary])
def list_prompts(db: Session = Depends(get_db)) -> list[PromptSummary]:
    prompts = db.execute(select(Prompt).order_by(Prompt.updated_at.desc())).scalars().all()
    pointers = db.execute(select(PromptActivePointer)).scalars().all()
    pointer_by_prompt = {item.prompt_id: item.active_version_id for item in pointers}

    version_rows = db.execute(select(PromptVersion.id, PromptVersion.version)).all()
    version_map = {row.id: row.version for row in version_rows}

    return [
        PromptSummary(
            prompt_key=prompt.prompt_key,
            description=prompt.description,
            owner_team=prompt.owner_team,
            updated_at=prompt.updated_at,
            active_version=version_map.get(pointer_by_prompt.get(prompt.id)),
        )
        for prompt in prompts
    ]


@router.get("/prompts/{prompt_key}", response_model=PromptDetail)
def get_prompt(prompt_key: str, db: Session = Depends(get_db)) -> PromptDetail:
    prompt = db.scalar(select(Prompt).where(Prompt.prompt_key == prompt_key))
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")

    pointer = db.get(PromptActivePointer, prompt.id)
    versions = db.execute(
        select(PromptVersion)
        .where(PromptVersion.prompt_id == prompt.id)
        .order_by(PromptVersion.version.desc())
    ).scalars()

    return PromptDetail(
        prompt_key=prompt.prompt_key,
        description=prompt.description,
        owner_team=prompt.owner_team,
        active_version_id=pointer.active_version_id if pointer else None,
        versions=[
            PromptVersionItem(
                id=row.id,
                version=row.version,
                status=row.status,
                checksum=row.checksum,
                content=row.content,
                variables_schema=row.variables_schema,
                created_by=row.created_by,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in versions
        ],
    )


@router.post("/prompts/{prompt_key}/draft")
def create_prompt_draft(prompt_key: str, body: DraftCreateRequest, db: Session = Depends(get_db)) -> dict:
    return create_draft(db, prompt_key, body)


@router.post("/prompts/{prompt_key}/publish", response_model=PublishResult)
def publish_prompt_version(
    prompt_key: str,
    body: PublishRequest,
    env: str = Query(default=settings.cms_environment),
    db: Session = Depends(get_db),
) -> PublishResult:
    result = publish_prompt(db, prompt_key, env, body.published_by)
    try:
        # Trigger one immediate dispatch attempt after publish.
        run_worker_once(db, limit=50)
    except Exception:  # noqa: BLE001
        # Publish transaction is already committed; worker failures are retried later.
        pass
    return result


@router.post("/prompts/{prompt_key}/rollback", response_model=PublishResult)
def rollback_prompt_version(
    prompt_key: str,
    body: RollbackRequest,
    env: str = Query(default=settings.cms_environment),
    db: Session = Depends(get_db),
) -> PublishResult:
    result = rollback_prompt(db, prompt_key, body.to_version, env, body.published_by)
    try:
        # Trigger one immediate dispatch attempt after rollback publish.
        run_worker_once(db, limit=50)
    except Exception:  # noqa: BLE001
        pass
    return result


@router.get("/publish-events", response_model=list[PublishEventItem])
def list_publish_events(
    prompt_key: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[PublishEventItem]:
    events_query = (
        select(PublishEvent, PromptVersion, Prompt)
        .join(PromptVersion, PromptVersion.id == PublishEvent.version_id)
        .join(Prompt, Prompt.id == PublishEvent.prompt_id)
        .order_by(PublishEvent.published_at.desc())
    )
    if prompt_key:
        events_query = events_query.where(Prompt.prompt_key == prompt_key)

    rows = db.execute(events_query).all()
    event_ids = [event.id for event, _, _ in rows]

    delivery_rows = []
    if event_ids:
        delivery_rows = db.execute(
            select(PushDelivery).where(PushDelivery.publish_event_id.in_(event_ids))
        ).scalars()

    deliveries_by_event: dict[int, list[PushDeliveryItem]] = {}
    for item in delivery_rows:
        deliveries_by_event.setdefault(item.publish_event_id, []).append(
            PushDeliveryItem(
                id=item.id,
                publish_event_id=item.publish_event_id,
                agent_id=item.agent_id,
                status=item.status,
                attempt=item.attempt,
                last_http_status=item.last_http_status,
                last_error=item.last_error,
                next_retry_at=item.next_retry_at,
                updated_at=item.updated_at,
            )
        )

    return [
        PublishEventItem(
            publish_event_id=event.id,
            prompt_key=prompt.prompt_key,
            version=version.version,
            environment=event.environment,
            published_by=event.published_by,
            published_at=event.published_at,
            deliveries=deliveries_by_event.get(event.id, []),
        )
        for event, version, prompt in rows
    ]
