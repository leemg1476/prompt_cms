import pytest


@pytest.mark.unit
def test_run_agent_with_bootstrap_prompt(client) -> None:
    response = client.post(
        "/api/agent/run",
        json={"prompt_key": "default.system", "user_input": "hello"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "user_input=hello" in body["output"]
    assert body["tracing_enabled"] is False


@pytest.mark.unit
def test_push_then_run_with_new_prompt(client) -> None:
    push_response = client.post(
        "/internal/prompts/push",
        headers={
            "Authorization": "Bearer local-dev-token",
            "Idempotency-Key": "event-1-agent-1",
        },
        json={
            "prompt_key": "stock.recommend.prepare",
            "version": 3,
            "checksum": "hash-3",
            "content": "SYSTEM: stock advisor",
        },
    )
    assert push_response.status_code == 200
    assert push_response.json()["applied"] is True
    assert push_response.json()["source"] == "yaml_file"

    files_response = client.get("/internal/prompts/files")
    assert files_response.status_code == 200
    assert any(name.endswith(".yml") for name in files_response.json()["files"])

    run_response = client.post(
        "/api/agent/run",
        json={"prompt_key": "stock.recommend.prepare", "user_input": "TSLA"},
    )
    assert run_response.status_code == 200
    assert "stock advisor" in run_response.json()["output"]


@pytest.mark.unit
def test_push_requires_idempotency(client) -> None:
    response = client.post(
        "/internal/prompts/push",
        headers={"Authorization": "Bearer local-dev-token"},
        json={
            "prompt_key": "stock.recommend.prepare",
            "version": 1,
            "checksum": "hash-1",
            "content": "SYSTEM: test",
        },
    )
    assert response.status_code == 400


@pytest.mark.unit
def test_tracing_status_endpoint(client) -> None:
    response = client.get("/api/agent/tracing")
    assert response.status_code == 200
    body = response.json()
    assert "langsmith_tracing" in body
    assert "has_api_key" in body
