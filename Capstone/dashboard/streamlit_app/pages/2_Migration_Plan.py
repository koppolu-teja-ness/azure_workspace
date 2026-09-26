from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import streamlit as st

API_BASE = os.getenv("MIGRATION_API_BASE_URL", "http://localhost:8000")


def _api_get(path: str) -> dict[str, Any]:
	request = Request(f"{API_BASE}{path}", method="GET")
	try:
		with urlopen(request, timeout=5) as response:
			return json.loads(response.read().decode("utf-8"))
	except (HTTPError, URLError, TimeoutError) as exc:
		raise RuntimeError(str(exc)) from exc


st.title("Migration Plan")
st.caption("Sequence and risk posture from the planning agent")

try:
	runs_response = _api_get("/approval/runs")
except RuntimeError as exc:
	st.error(f"Could not reach API at {API_BASE}: {exc}")
	st.stop()

runs = runs_response.get("runs", [])
if not runs:
	st.warning("No runs available yet.")
	st.stop()

run_ids = [str(item.get("run_id", "")) for item in runs]
selected_run_id = st.selectbox("Run", options=run_ids)

try:
	run_state = _api_get(f"/approval/runs/{selected_run_id}")
except RuntimeError as exc:
	st.error(f"Could not fetch run details: {exc}")
	st.stop()

plan = run_state.get("config", {}).get("migration_plan", {})
risk_summary = plan.get("risk_summary", {})

col1, col2, col3, col4 = st.columns(4)
col1.metric("Resources", plan.get("resource_count", 0))
col2.metric("Auto", risk_summary.get("auto_migratable", 0))
col3.metric("Needs Review", risk_summary.get("needs_review", 0))
col4.metric("High Risk", risk_summary.get("high_risk", 0))

st.subheader("Execution Sequence")
sequence = plan.get("sequence", [])
if sequence:
	st.dataframe(sequence, use_container_width=True, hide_index=True)
else:
	st.info("No sequencing metadata available for this run.")

st.subheader("Risk Assessments")
risk_rows = run_state.get("risk_assessments", [])
if risk_rows:
	st.dataframe(risk_rows, use_container_width=True, hide_index=True)
else:
	st.info("No risk assessments available.")
