from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import streamlit as st

API_BASE = os.getenv("MIGRATION_API_BASE_URL", "http://localhost:8000")


def _api_get(path: str) -> dict[str, Any]:
    request = Request(f"{API_BASE}{path}", method="GET")
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(str(exc)) from exc


def _api_post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = Request(
        f"{API_BASE}{path}",
        method="POST",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload).encode("utf-8"),
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(str(exc)) from exc


st.title("Discovery")
st.caption("Run discovery + planning pipeline (Bedrock required) and inspect source inventory")

default_run_id = f"run-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"
default_model_id = os.getenv("BEDROCK_MODEL_ID", "")
default_region = os.getenv("BEDROCK_REGION", os.getenv("AWS_REGION", "us-east-1"))

if "readiness_checked_at" not in st.session_state:
    st.session_state["readiness_checked_at"] = datetime.now(UTC).strftime("%H:%M:%S UTC")

if st.button("Refresh Readiness", key="refresh_readiness"):
    st.session_state["readiness_checked_at"] = datetime.now(UTC).strftime("%H:%M:%S UTC")
    st.rerun()

st.subheader("Runtime Readiness")
bedrock_ready = bool(default_model_id.strip())
api_ready = False
db_ready = False
run_count = 0
db_error = ""

try:
    health_payload = _api_get("/health")
    api_ready = True
    db_ready = health_payload.get("db_status") == "ok"
    run_count = int(health_payload.get("runs", 0))
    db_error = str(health_payload.get("db_error", ""))
except RuntimeError as exc:
    db_error = str(exc)

readiness_col1, readiness_col2, readiness_col3 = st.columns(3)
readiness_col1.metric("Bedrock Config", "Ready" if bedrock_ready else "Missing")
readiness_col2.metric("API Connectivity", "Connected" if api_ready else "Disconnected")
readiness_col3.metric("Postgres Readiness", "Ready" if db_ready else "Unavailable")

if api_ready and db_ready:
    st.caption(f"Run store reachable. Existing runs in DB: {run_count}")
else:
    st.warning(
        "Runtime not fully ready. Check API process, Postgres container, "
        "and DATABASE_URL before running discovery."
    )
    if db_error:
        st.caption(f"Last connectivity detail: {db_error}")

st.caption(f"Last checked: {st.session_state['readiness_checked_at']}")

with st.form("discovery_form"):
    run_id = st.text_input("Run ID", value=default_run_id)
    bicep_paths_text = st.text_area(
        "Bicep file paths (one per line)",
        placeholder="examples/sample_migration_run/input_bicep/main.bicep",
    )
    bicep_dirs_text = st.text_area(
        "Bicep directories (one per line)",
        placeholder="tests/fixtures/sample_bicep",
    )
    st.subheader("Bedrock LLM Configuration")
    model_id = st.text_input(
        "Model ID",
        value=default_model_id,
        placeholder="anthropic.claude-3-5-sonnet-20240620-v1:0",
    )
    region_name = st.text_input("Region", value=default_region)
    col1, col2 = st.columns(2)
    temperature = col1.number_input("Temperature", min_value=0.0, max_value=1.0, value=0.7)
    max_tokens = col2.number_input("Max Tokens", min_value=64, max_value=8192, value=800, step=64)
    auto_approve = st.checkbox("Auto-approve run", value=False)
    submitted = st.form_submit_button("Run Discovery")

if submitted:
    run_id = run_id.strip()
    if not run_id:
        st.error("Run ID is required.")
        st.stop()
    model_id = model_id.strip()
    region_name = region_name.strip()
    if not model_id:
        st.error("Bedrock model ID is required.")
        st.stop()
    if not region_name:
        st.error("Bedrock region is required.")
        st.stop()

    bicep_paths = [line.strip() for line in bicep_paths_text.splitlines() if line.strip()]
    bicep_directories = [line.strip() for line in bicep_dirs_text.splitlines() if line.strip()]

    payload = {
        "run_id": run_id,
        "bicep_paths": bicep_paths,
        "bicep_directories": bicep_directories,
        "config": {
            "approval": {"auto_approve": auto_approve},
            "llm": {
                "enabled": True,
                "provider": "aws_bedrock",
                "bedrock": {
                    "model_id": model_id,
                    "region_name": region_name,
                    "temperature": float(temperature),
                    "max_tokens": int(max_tokens),
                },
            },
        },
    }
    try:
        result = _api_post("/discovery/runs", payload)
        st.success(f"Run '{run_id}' executed.")
        st.json(
            {
                "run_id": result.get("run_id"),
                "status": result.get("status"),
                "source_resources": len(result.get("source_resources", [])),
                "mappings": len(result.get("mappings", [])),
            }
        )
    except RuntimeError as exc:
        st.error(f"Discovery execution failed: {exc}")

try:
    runs_response = _api_get("/discovery/runs")
except RuntimeError as exc:
    st.error(f"Could not reach API at {API_BASE}: {exc}")
    st.stop()

runs = runs_response.get("runs", [])
if not runs:
    st.info("No runs available yet.")
    st.stop()

run_ids = [str(item.get("run_id", "")) for item in runs]
selected_run_id = st.selectbox("Inspect Run", options=run_ids)

try:
    run_state = _api_get(f"/discovery/runs/{selected_run_id}")
except RuntimeError as exc:
    st.error(f"Could not fetch run details: {exc}")
    st.stop()

config = run_state.get("config", {})
discovered_files = config.get("discovered_bicep_files", [])

col1, col2, col3 = st.columns(3)
col1.metric("Discovered Files", len(discovered_files))
col2.metric("Source Resources", len(run_state.get("source_resources", [])))
col3.metric("Mappings", len(run_state.get("mappings", [])))

st.subheader("Discovered Bicep Files")
if discovered_files:
    st.dataframe(
        [{"path": path} for path in discovered_files], hide_index=True, use_container_width=True
    )
else:
    st.info("No Bicep files discovered for this run.")

st.subheader("Source Resources")
source_resources = run_state.get("source_resources", [])
if source_resources:
    rows = [
        {
            "resource_id": item.get("resource_id"),
            "resource_type": item.get("resource_type"),
            "name": item.get("name"),
            "location": item.get("location"),
        }
        for item in source_resources
    ]
    st.dataframe(rows, hide_index=True, use_container_width=True)
else:
    st.info("No source resources parsed yet.")
