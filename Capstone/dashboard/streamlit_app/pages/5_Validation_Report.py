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
		with urlopen(request, timeout=10) as response:
			return json.loads(response.read().decode("utf-8"))
	except (HTTPError, URLError, TimeoutError) as exc:
		raise RuntimeError(str(exc)) from exc


st.title("Validation Report")
st.caption("Review migration plan, execution, and validation reports for each run")

try:
	runs_response = _api_get("/approval/runs")
except RuntimeError as exc:
	st.error(f"Could not reach API at {API_BASE}: {exc}")
	st.stop()

runs = runs_response.get("runs", [])
if not runs:
	st.info("No runs available yet.")
	st.stop()

run_ids = [str(item.get("run_id", "")) for item in runs]
selected_run_id = st.selectbox("Run", options=run_ids)

try:
	reports_payload = _api_get(f"/reports/runs/{selected_run_id}")
except RuntimeError as exc:
	st.error(f"Could not load reports: {exc}")
	st.stop()

col1, col2 = st.columns(2)
col1.metric("Run ID", str(reports_payload.get("run_id", "-")))
col2.metric("Status", str(reports_payload.get("status", "unknown")))

summary = reports_payload.get("report_summary")
if summary:
	st.subheader("Summary")
	st.write(summary)

reports = reports_payload.get("reports", {})

st.subheader("Validation Report")
st.json(reports.get("validation_report", {}))

st.subheader("Execution Report")
st.json(reports.get("execution_report", {}))

st.subheader("Risk Report")
st.json(reports.get("risk_report", {}))

st.subheader("Migration Plan Report")
st.json(reports.get("migration_plan_report", {}))
