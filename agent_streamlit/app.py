import json
import os

import requests
import streamlit as st

AGENT_BASE_URL = os.getenv("AGENT_BASE_URL", "http://localhost:8010")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
PUSH_AUTH_TOKEN = os.getenv("PUSH_AUTH_TOKEN", "local-dev-token")


def call_json(method: str, url: str, **kwargs):
    response = requests.request(method=method, url=url, timeout=20, **kwargs)
    response.raise_for_status()
    if response.headers.get("content-type", "").startswith("application/json"):
        return response.json()
    return {"text": response.text}


st.set_page_config(page_title="Prompt Agent Console", layout="wide")
st.title("Prompt Agent Console")

col_a, col_b = st.columns(2)
with col_a:
    st.caption(f"Agent API: `{AGENT_BASE_URL}`")
with col_b:
    st.caption(f"Backend API: `{BACKEND_BASE_URL}`")

st.subheader("1) Agent Tracing Status")
if st.button("Refresh Tracing Status"):
    try:
        status = call_json("GET", f"{AGENT_BASE_URL}/api/agent/tracing")
        st.json(status)
    except Exception as exc:  # noqa: BLE001
        st.error(str(exc))

st.subheader("2) Run Agent")
prompt_key = st.text_input("Prompt Key", value="default.system")
user_input = st.text_area("User Input", value="AAPL 분석해줘")
trace_name = st.text_input("Trace Name (optional)", value="streamlit-agent-run")
trace_tags_str = st.text_input("Trace Tags (comma-separated)", value="streamlit,manual-test")
trace_metadata_str = st.text_area(
    "Trace Metadata JSON (optional)",
    value='{"source":"streamlit","tester":"local"}',
)

if st.button("Run Agent"):
    try:
        trace_tags = [tag.strip() for tag in trace_tags_str.split(",") if tag.strip()]
        trace_metadata = json.loads(trace_metadata_str) if trace_metadata_str.strip() else None
        body = {
            "prompt_key": prompt_key,
            "user_input": user_input,
            "trace_name": trace_name or None,
            "trace_tags": trace_tags or None,
            "trace_metadata": trace_metadata,
        }
        result = call_json("POST", f"{AGENT_BASE_URL}/api/agent/run", json=body)
        st.success("Agent run completed")
        st.json(result)
    except Exception as exc:  # noqa: BLE001
        st.error(str(exc))

st.subheader("3) Agent Cache / YAML Files")
col1, col2 = st.columns(2)
with col1:
    if st.button("Load Agent Cache"):
        try:
            cache = call_json("GET", f"{AGENT_BASE_URL}/internal/prompts/cache")
            st.json(cache)
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))
with col2:
    if st.button("Load YAML Files"):
        try:
            files = call_json("GET", f"{AGENT_BASE_URL}/internal/prompts/files")
            st.json(files)
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))

st.subheader("4) Publish Helper (Backend -> Agent)")
helper_prompt_key = st.text_input("Helper Prompt Key", value="stock.recommend.prepare")
helper_content = st.text_area("Draft Content", value="SYSTEM: streamlit helper prompt")
helper_env = st.selectbox("Publish Env", ["dev", "stg", "prod"], index=0)
helper_user = st.text_input("Actor", value="streamlit")

if st.button("Create Draft -> Publish -> Run Worker Once"):
    try:
        draft_body = {
            "content": helper_content,
            "variables_schema": {"type": "object", "properties": {"ticker": {"type": "string"}}},
            "created_by": helper_user,
            "description": "created from streamlit helper",
            "owner_team": "qa",
        }
        draft = call_json("POST", f"{BACKEND_BASE_URL}/api/prompts/{helper_prompt_key}/draft", json=draft_body)
        publish = call_json(
            "POST",
            f"{BACKEND_BASE_URL}/api/prompts/{helper_prompt_key}/publish?env={helper_env}",
            json={"published_by": helper_user},
        )
        worker = call_json("POST", f"{BACKEND_BASE_URL}/api/worker/run-once")
        st.success("Publish flow completed")
        st.json({"draft": draft, "publish": publish, "worker": worker})
    except Exception as exc:  # noqa: BLE001
        st.error(str(exc))

st.subheader("5) Manual Push to Agent (Optional)")
manual_push_key = st.text_input("Manual Push Prompt Key", value="manual.push.sample")
manual_push_content = st.text_area("Manual Push Content", value="SYSTEM: manual push")
if st.button("Push Directly to Agent"):
    try:
        payload = {
            "prompt_key": manual_push_key,
            "version": 1,
            "checksum": "manual-checksum",
            "content": manual_push_content,
            "variables_schema": None,
            "deployment_mode": "yaml_file_sync",
        }
        result = call_json(
            "POST",
            f"{AGENT_BASE_URL}/internal/prompts/push",
            json=payload,
            headers={
                "Authorization": f"Bearer {PUSH_AUTH_TOKEN}",
                "Idempotency-Key": "streamlit-manual-1",
            },
        )
        st.success("Manual push completed")
        st.json(result)
    except Exception as exc:  # noqa: BLE001
        st.error(str(exc))
