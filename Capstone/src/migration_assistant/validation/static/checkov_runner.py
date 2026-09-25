"""Run checkov against generated CloudFormation templates."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from migration_assistant.graph.state import (
	ValidationResult,
	ValidationStage,
	ValidationStatus,
)


def run_checkov(template_path: Path, *, run_id: str) -> list[ValidationResult]:
	"""Execute checkov policy checks and normalize the findings."""
	completed = _run_command(
		[
			"checkov",
			"--framework",
			"cloudformation",
			"--file",
			str(template_path),
			"--output",
			"json",
			"--quiet",
		],
		[
			sys.executable,
			"-m",
			"checkov.main",
			"--framework",
			"cloudformation",
			"--file",
			str(template_path),
			"--output",
			"json",
			"--quiet",
		],
	)

	if completed is None:
		return [
			ValidationResult(
				stage=ValidationStage.STATIC,
				resource_id=run_id,
				check_name="checkov",
				status=ValidationStatus.WARNING,
				details=(
					"checkov is not installed. Install checkov to enable "
					"static security policy checks."
				),
			)
		]

	reports = _extract_reports(completed.stdout)
	failed_results = _build_failed_results(reports, run_id=run_id)
	if failed_results:
		return failed_results

	if reports:
		summary = _summarize_reports(reports)
		return [
			ValidationResult(
				stage=ValidationStage.STATIC,
				resource_id=run_id,
				check_name="checkov",
				status=ValidationStatus.PASS,
				details=(
					"checkov found no failed checks "
					f"(passed={summary['passed']}, skipped={summary['skipped']})."
				),
			)
		]

	if completed.returncode == 0:
		return [
			ValidationResult(
				stage=ValidationStage.STATIC,
				resource_id=run_id,
				check_name="checkov",
				status=ValidationStatus.PASS,
				details="checkov completed with no failed checks.",
			)
		]

	details = (completed.stderr or completed.stdout).strip() or "checkov execution failed"
	return [
		ValidationResult(
			stage=ValidationStage.STATIC,
			resource_id=run_id,
			check_name="checkov",
			status=ValidationStatus.FAIL,
			details=_truncate(details),
		)
	]


def _run_command(
	primary_command: list[str],
	fallback_command: list[str],
) -> subprocess.CompletedProcess[str] | None:
	for command in (primary_command, fallback_command):
		try:
			return subprocess.run(
				command,
				check=False,
				capture_output=True,
				text=True,
			)
		except FileNotFoundError:
			continue
	return None


def _extract_reports(raw_output: str) -> list[dict[str, Any]]:
	payload = _parse_json_payload(raw_output)
	if payload is None:
		return []

	if isinstance(payload, list):
		return [entry for entry in payload if isinstance(entry, dict)]

	if isinstance(payload, dict):
		if isinstance(payload.get("results"), dict):
			return [payload]
		if isinstance(payload.get("reports"), list):
			return [entry for entry in payload["reports"] if isinstance(entry, dict)]
	return []


def _build_failed_results(reports: list[dict[str, Any]], *, run_id: str) -> list[ValidationResult]:
	results: list[ValidationResult] = []
	for report in reports:
		report_results = report.get("results", {})
		if not isinstance(report_results, dict):
			continue

		failed_checks = report_results.get("failed_checks", [])
		if not isinstance(failed_checks, list):
			continue

		for finding in failed_checks:
			if not isinstance(finding, dict):
				continue
			check_id = str(finding.get("check_id") or "checkov")
			check_name = str(finding.get("check_name") or "policy check")
			resource_id = _normalize_resource_id(finding.get("resource"), default=run_id)

			line_range = finding.get("file_line_range")
			line_suffix = ""
			if isinstance(line_range, list) and len(line_range) == 2:
				start, end = line_range
				line_suffix = f" (lines {start}-{end})"

			guideline = finding.get("guideline")
			guideline_suffix = f" Guideline: {guideline}" if isinstance(guideline, str) else ""
			details = _truncate(f"{check_name}{line_suffix}.{guideline_suffix}".strip())

			results.append(
				ValidationResult(
					stage=ValidationStage.STATIC,
					resource_id=resource_id,
					check_name=check_id,
					status=ValidationStatus.FAIL,
					details=details,
				)
			)
	return results


def _normalize_resource_id(value: Any, *, default: str) -> str:
	if not isinstance(value, str) or not value:
		return default
	if value.startswith("Resources."):
		return value.split(".", 1)[1]
	return value


def _summarize_reports(reports: list[dict[str, Any]]) -> dict[str, int]:
	counts = {"passed": 0, "failed": 0, "skipped": 0}
	for report in reports:
		summary = report.get("summary")
		if not isinstance(summary, dict):
			continue
		for key in counts:
			value = summary.get(key)
			if isinstance(value, int):
				counts[key] += value
	return counts


def _parse_json_payload(raw_output: str) -> Any | None:
	stripped = raw_output.strip()
	if not stripped:
		return None

	try:
		return json.loads(stripped)
	except json.JSONDecodeError:
		pass

	start_obj = stripped.find("{")
	end_obj = stripped.rfind("}")
	if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
		candidate = stripped[start_obj : end_obj + 1]
		try:
			return json.loads(candidate)
		except json.JSONDecodeError:
			return None

	start_arr = stripped.find("[")
	end_arr = stripped.rfind("]")
	if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
		candidate = stripped[start_arr : end_arr + 1]
		try:
			return json.loads(candidate)
		except json.JSONDecodeError:
			return None
	return None


def _truncate(value: str, *, limit: int = 500) -> str:
	compact = " ".join(value.split())
	if len(compact) <= limit:
		return compact
	return compact[: limit - 3] + "..."
