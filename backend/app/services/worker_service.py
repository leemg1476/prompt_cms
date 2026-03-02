from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import AgentRegistry, Prompt, PromptVersion, PublishEvent, PushDelivery
from app.schemas.prompts import WorkerRunResult

BACKOFF_MINUTES = [1, 2, 5, 10, 30, 60]
MAX_ATTEMPTS = 10


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _compute_next_retry(attempt: int) -> datetime:
    index = min(max(attempt - 1, 0), len(BACKOFF_MINUTES) - 1)
    return utcnow() + timedelta(minutes=BACKOFF_MINUTES[index])


def run_worker_once(db: Session, limit: int = 50) -> WorkerRunResult:
    now = utcnow()
    rows = db.execute(
        select(PushDelivery, AgentRegistry, PublishEvent, PromptVersion, Prompt)
        .join(AgentRegistry, AgentRegistry.id == PushDelivery.agent_id)
        .join(PublishEvent, PublishEvent.id == PushDelivery.publish_event_id)
        .join(PromptVersion, PromptVersion.id == PublishEvent.version_id)
        .join(Prompt, Prompt.id == PublishEvent.prompt_id)
        .where(
            PushDelivery.status == "pending",
            or_(PushDelivery.next_retry_at.is_(None), PushDelivery.next_retry_at <= now),
            AgentRegistry.is_enabled.is_(True),
        )
        .limit(limit)
    ).all()

    processed = 0
    succeeded = 0
    failed = 0
    still_pending = 0

    with httpx.Client(timeout=10.0) as client:
        for delivery, agent, event, version, prompt in rows:
            processed += 1
            delivery.attempt += 1

            payload = {
                "prompt_key": prompt.prompt_key,
                "version": version.version,
                "checksum": version.checksum,
                "content": version.content,
                "variables_schema": version.variables_schema,
                "published_at": event.published_at.isoformat(),
                "deployment_mode": "yaml_file_sync",
            }

            headers = {
                "Authorization": f"Bearer {settings.push_auth_token}",
                "Idempotency-Key": delivery.idempotency_key,
            }
            url = f"{agent.base_url.rstrip('/')}{agent.push_endpoint}"

            response = None
            try:
                response = client.post(url, json=payload, headers=headers)
                body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                ok = response.status_code == 200 and body.get("ok") is True

                if ok:
                    delivery.status = "success"
                    delivery.last_http_status = response.status_code
                    delivery.last_error = None
                    delivery.next_retry_at = None
                    succeeded += 1
                else:
                    _mark_failure_or_retry(delivery, response.status_code, f"Unexpected response: {body}")
                    if delivery.status == "failed":
                        failed += 1
                    else:
                        still_pending += 1
            except Exception as exc:  # noqa: BLE001
                status_code = response.status_code if response is not None else None
                _mark_failure_or_retry(delivery, status_code, str(exc))
                if delivery.status == "failed":
                    failed += 1
                else:
                    still_pending += 1

            delivery.updated_at = utcnow()

    db.commit()
    return WorkerRunResult(
        processed=processed,
        succeeded=succeeded,
        failed=failed,
        still_pending=still_pending,
    )


def _mark_failure_or_retry(delivery: PushDelivery, http_status: int | None, error: str) -> None:
    delivery.last_http_status = http_status
    delivery.last_error = error

    is_4xx = http_status is not None and 400 <= http_status < 500
    if is_4xx or delivery.attempt >= MAX_ATTEMPTS:
        delivery.status = "failed"
        delivery.next_retry_at = None
        return

    delivery.status = "pending"
    delivery.next_retry_at = _compute_next_retry(delivery.attempt)
