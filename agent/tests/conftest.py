import pathlib
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app.services.store import prompt_store  # noqa: E402


@pytest.fixture(autouse=True)
def clear_store() -> None:
    prompt_store.cache.clear()
    prompt_store.idempotency_seen.clear()
    prompt_store.upsert(
        prompt_key="default.system",
        version=1,
        checksum="bootstrapped",
        content="SYSTEM: You are a test LangGraph agent.",
        variables_schema=None,
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
