from datetime import datetime, timezone

import pytest

from app.models.entities import PushDelivery
from app.services.worker_service import _compute_next_retry, _mark_failure_or_retry


def _delivery() -> PushDelivery:
    return PushDelivery(
        publish_event_id=1,
        agent_id=1,
        idempotency_key="1-1",
        attempt=1,
        status="pending",
    )


@pytest.mark.unit
def test_compute_next_retry_returns_future() -> None:
    now = datetime.now(timezone.utc)
    next_retry = _compute_next_retry(1)
    assert next_retry > now


@pytest.mark.unit
def test_mark_failure_4xx_sets_failed() -> None:
    delivery = _delivery()
    _mark_failure_or_retry(delivery, 400, "bad request")
    assert delivery.status == "failed"
    assert delivery.next_retry_at is None


@pytest.mark.unit
def test_mark_failure_5xx_keeps_pending_with_retry() -> None:
    delivery = _delivery()
    _mark_failure_or_retry(delivery, 503, "service unavailable")
    assert delivery.status == "pending"
    assert delivery.next_retry_at is not None
