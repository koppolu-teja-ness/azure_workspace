"""Run cfn-lint against generated CloudFormation templates."""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

from migration_assistant.graph.state import (
	ValidationResult,
	ValidationStage,
	ValidationStatus,
)

logger = logging.getLogger(__name__)


def run_cfn_lint(template_path: Path, *, run_id: str) -> list[ValidationResult]:
	"""Execute cfn-lint and convert findings into ValidationResult entries."""
	completed = _run_command(
		["cfn-lint", "--format", "json", str(template_path)],
		[sys.executable, "-m", "cfnlint", "--format", "json", str(template_path)],
	)

	if completed is None:
		return [
			ValidationResult(
				stage=ValidationStage.STATIC,
				resource_id=run_id,
				check_name="cfn-lint",
				status=ValidationStatus.WARNING,
				details=(
					"cfn-lint is not installed. Install cfn-lint to enable "
					"CloudFormation lint checks."
				),
			)
		]

	findings = _parse_lint_findings(completed.stdout, run_id=run_id)
	if findings:
		return findings

	if completed.returncode == 0:
		return [
			ValidationResult(
				stage=ValidationStage.STATIC,
				resource_id=run_id,
				check_name="cfn-lint",
				status=ValidationStatus.PASS,
				details="cfn-lint found no syntax or schema issues.",
			)
		]

	details = (completed.stderr or completed.stdout).strip() or "cfn-lint execution failed"
	logger.warning("cfn_lint_runner: execution failed with code %s", completed.returncode)
	return [
		ValidationResult(
			stage=ValidationStage.STATIC,
			resource_id=run_id,
			check_name="cfn-lint",
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


def _parse_lint_findings(raw_output: str, *, run_id: str) -> list[ValidationResult]:
	payload = _parse_json_payload(raw_output)
	if payload is None:
		return []

	matches: list[dict[str, Any]] = []
	if isinstance(payload, list):
		matches = [entry for entry in payload if isinstance(entry, dict)]
	elif isinstance(payload, dict):
		raw_matches = payload.get("matches", [])
		if isinstance(raw_matches, list):
			matches = [entry for entry in raw_matches if isinstance(entry, dict)]

	results: list[ValidationResult] = []
	for match in matches:
		rule = match.get("Rule")
		if isinstance(rule, dict):
			check_name = str(rule.get("Id") or "cfn-lint")
		else:
			check_name = "cfn-lint"

		level = str(match.get("Level", "Error")).lower()
		status = ValidationStatus.FAIL if level == "error" else ValidationStatus.WARNING

		message = str(match.get("Message") or "cfn-lint finding")
		location = match.get("Location")
		resource_id = _extract_resource_id(location, default=run_id)
		details = _build_detail(message=message, location=location)

		results.append(
			ValidationResult(
				stage=ValidationStage.STATIC,
				resource_id=resource_id,
				check_name=check_name,
				status=status,
				details=details,
			)
		)

	return results


def _extract_resource_id(location: Any, *, default: str) -> str:
	if not isinstance(location, dict):
		return default
	path = location.get("Path")
	if isinstance(path, list) and len(path) > 1 and path[0] == "Resources":
		logical_id = path[1]
		if isinstance(logical_id, str):
			return logical_id
	return default


def _build_detail(*, message: str, location: Any) -> str:
	if not isinstance(location, dict):
		return _truncate(message)

	path = location.get("Path")
	start = location.get("Start")
	line_number = None
	if isinstance(start, dict):
		line_number = start.get("LineNumber")

	parts = [message]
	if isinstance(path, list) and path:
		parts.append(f"path={'.'.join(str(part) for part in path)}")
	if isinstance(line_number, int):
		parts.append(f"line={line_number}")
	return _truncate(" | ".join(parts))


def _parse_json_payload(raw_output: str) -> Any | None:
	stripped = raw_output.strip()
	if not stripped:
		return None

	try:
		return json.loads(stripped)
	except json.JSONDecodeError:
		pass

	candidates: list[str] = []

	start_obj = stripped.find("{")
	end_obj = stripped.rfind("}")
	if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
		candidates.append(stripped[start_obj : end_obj + 1])

	start_arr = stripped.find("[")
	end_arr = stripped.rfind("]")
	if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
		candidates.append(stripped[start_arr : end_arr + 1])

	for candidate in candidates:
		try:
			return json.loads(candidate)
		except json.JSONDecodeError:
			continue
	return None


def _truncate(value: str, *, limit: int = 500) -> str:
	compact = " ".join(value.split())
	if len(compact) <= limit:
		return compact
	return compact[: limit - 3] + "..."
