import pathlib
import sys

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from app.main import app
from app.services.agent_store import prompt_store


@pytest.fixture(autouse=True)
def clear_prompt_store() -> None:
    prompt_store.cache.clear()


@pytest.fixture
def app_instance():
    return app


@pytest_asyncio.fixture
async def client(app_instance):
    transport = ASGITransport(app=app_instance)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer local-dev-token"}
