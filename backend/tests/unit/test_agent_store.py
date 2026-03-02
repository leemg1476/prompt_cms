import pytest

from app.services.agent_store import prompt_store


@pytest.mark.unit
def test_prompt_store_upsert_and_get() -> None:
    prompt_store.upsert(
        prompt_key="stock.recommend.prepare",
        version=2,
        checksum="abc123",
        content="SYSTEM: prompt",
        variables_schema={"type": "object"},
    )
    cached = prompt_store.get("stock.recommend.prepare")
    assert cached is not None
    assert cached.version == 2
    assert cached.checksum == "abc123"
