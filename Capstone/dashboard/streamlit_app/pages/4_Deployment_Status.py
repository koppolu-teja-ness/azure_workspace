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


def _api_post(path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
	request = Request(
		f"{API_BASE}{path}",
		method="POST",
		headers={"Content-Type": "application/json"},
		data=json.dumps(payload or {}).encode("utf-8"),
	)
	try:
		with urlopen(request, timeout=30) as response:
			return json.loads(response.read().decode("utf-8"))
	except (HTTPError, URLError, TimeoutError) as exc:
		raise RuntimeError(str(exc)) from exc


st.title("Deployment Status")
st.caption("Execute target-side stages and inspect deployment previews/results")

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

if st.button("Execute Target Pipeline", type="primary"):
	try:
		result = _api_post(f"/runs/{selected_run_id}/execute-target")
		st.success(f"Target pipeline executed for '{selected_run_id}'.")
		st.json(
			{
				"run_id": result.get("run_id"),
				"status": result.get("status"),
				"target_resources": len(result.get("target_resources", [])),
				"validation_results": len(result.get("validation_results", [])),
			}
		)
	except RuntimeError as exc:
		st.error(f"Target pipeline execution failed: {exc}")

try:
	run_state = _api_get(f"/runs/{selected_run_id}")
except RuntimeError as exc:
	st.error(f"Could not fetch run details: {exc}")
	st.stop()

config = run_state.get("config", {})
preview = config.get("deployment_preview")
result = config.get("deployment_result")

col1, col2, col3 = st.columns(3)
col1.metric("Run Status", str(run_state.get("status", "unknown")))
col2.metric("Target Resources", len(run_state.get("target_resources", [])))
col3.metric("Validation Results", len(run_state.get("validation_results", [])))

st.subheader("Deployment Output")
if preview:
	st.markdown("Dry-run preview")
	st.json(preview)
elif result:
	st.markdown("Live deployment result")
	st.json(result)
else:
	st.info("No deployment output found yet. Run target pipeline first.")

st.subheader("Target Resources")
target_resources = run_state.get("target_resources", [])
if target_resources:
	rows = [
		{
			"logical_id": item.get("logical_id"),
			"type": item.get("aws_resource_type"),
			"depends_on": len(item.get("depends_on", [])),
		}
		for item in target_resources
	]
	st.dataframe(rows, hide_index=True, use_container_width=True)
else:
	st.info("No target resources generated yet.")

st.subheader("Validation Results")
validation_results = run_state.get("validation_results", [])
if validation_results:
	rows = [
		{
			"stage": item.get("stage"),
			"check": item.get("check_name"),
			"status": item.get("status"),
			"details": item.get("details"),
		}
		for item in validation_results
	]
	st.dataframe(rows, hide_index=True, use_container_width=True)
else:
	st.info("No validation results available yet.")
