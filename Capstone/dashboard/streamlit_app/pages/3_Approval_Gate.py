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


def _api_post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
	request = Request(
		f"{API_BASE}{path}",
		method="POST",
		headers={"Content-Type": "application/json"},
		data=json.dumps(payload).encode("utf-8"),
	)
	try:
		with urlopen(request, timeout=5) as response:
			return json.loads(response.read().decode("utf-8"))
	except (HTTPError, URLError, TimeoutError) as exc:
		raise RuntimeError(str(exc)) from exc


st.title("Approval Gate")
st.caption("Approve, reject, or request modification for a migration run")

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

approval = run_state.get("approval", {})
status = run_state.get("status", "unknown")
risk_items = run_state.get("risk_assessments", [])
high_risk = [item for item in risk_items if item.get("risk_level") == "high_risk"]

col1, col2, col3 = st.columns(3)
col1.metric("Current Status", status)
col2.metric("Risk Assessments", len(risk_items))
col3.metric("High Risk", len(high_risk))

with st.expander("Current Decision", expanded=True):
	st.json(approval)

if high_risk:
	st.warning("High-risk resources detected. Reviewer comments are strongly recommended.")

with st.form("approval_form"):
	reviewer = st.text_input("Reviewer", value="")
	decision = st.radio(
		"Decision",
		options=["approved", "rejected", "modified"],
		horizontal=True,
	)
	comments = st.text_area("Comments", height=120)
	submitted = st.form_submit_button("Submit Decision")

if submitted:
	reviewer = reviewer.strip()
	if not reviewer:
		st.error("Reviewer is required.")
		st.stop()

	payload = {
		"decision": decision,
		"reviewer": reviewer,
		"comments": comments.strip() or None,
	}
	try:
		result = _api_post(f"/approval/runs/{selected_run_id}/decision", payload)
	except RuntimeError as exc:
		st.error(f"Could not submit decision: {exc}")
		st.stop()

	st.success("Decision submitted.")
	st.json(result)
