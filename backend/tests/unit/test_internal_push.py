import pytest
from sqlalchemy.exc import IntegrityError

from app.core.db import get_db
from app.main import app


class FakeDB:
    def __init__(self) -> None:
        self.seen: set[str] = set()
        self.pending_key: str | None = None

    def add(self, row) -> None:
        self.pending_key = row.idempotency_key

    def commit(self) -> None:
        if self.pending_key is None:
            return
        if self.pending_key in self.seen:
            raise IntegrityError("insert", {}, Exception("duplicate"))
        self.seen.add(self.pending_key)
        self.pending_key = None

    def rollback(self) -> None:
        self.pending_key = None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_internal_push_applies_new_prompt(client, auth_headers) -> None:
    fake_db = FakeDB()
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        response = await client.post(
            "/internal/prompts/push",
            headers={**auth_headers, "Idempotency-Key": "event-1-agent-1"},
            json={
                "prompt_key": "stock.recommend.prepare",
                "version": 1,
                "checksum": "hash-1",
                "content": "SYSTEM: hello",
                "variables_schema": {"type": "object"},
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        assert body["applied"] is True
        assert body["cache_state"] == "updated"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_internal_push_duplicate_idempotency_returns_already_processed(client, auth_headers) -> None:
    fake_db = FakeDB()
    app.dependency_overrides[get_db] = lambda: fake_db
    headers = {**auth_headers, "Idempotency-Key": "event-2-agent-1"}
    payload = {
        "prompt_key": "stock.recommend.prepare",
        "version": 2,
        "checksum": "hash-2",
        "content": "SYSTEM: v2",
    }
    try:
        first = await client.post("/internal/prompts/push", headers=headers, json=payload)
        second = await client.post("/internal/prompts/push", headers=headers, json=payload)
        assert first.status_code == 200
        assert second.status_code == 200
        assert second.json()["applied"] is False
        assert second.json()["cache_state"] == "already_processed"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_internal_push_requires_idempotency_key(client, auth_headers) -> None:
    fake_db = FakeDB()
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        response = await client.post(
            "/internal/prompts/push",
            headers=auth_headers,
            json={
                "prompt_key": "stock.recommend.prepare",
                "version": 1,
                "checksum": "hash-1",
                "content": "SYSTEM: hello",
            },
        )
        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()
