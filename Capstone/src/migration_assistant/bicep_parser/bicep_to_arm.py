"""Optional Azure CLI-backed Bicep compile helpers.

This module is intentionally best-effort: local parser paths must still work
when Azure CLI is unavailable.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any


@dataclass(frozen=True, slots=True)
class ArmCompileResult:
	resources: list[dict[str, Any]]
	provenance: str


def azure_cli_available() -> bool:
	return shutil.which("az") is not None


def compile_bicep_file_to_arm_resources(file_path: str) -> ArmCompileResult | None:
	"""Compile a Bicep file via `az bicep build` and return ARM resources.

	Returns None when Azure CLI is unavailable or compilation fails.
	"""
	if not azure_cli_available():
		return None

	bicep_path = Path(file_path).expanduser().resolve()
	if not bicep_path.is_file():
		return None

	with TemporaryDirectory(prefix="migration-bicep-build-") as temp_dir:
		output_path = Path(temp_dir) / f"{bicep_path.stem}.json"
		command = [
			"az",
			"bicep",
			"build",
			"--file",
			str(bicep_path),
			"--outfile",
			str(output_path),
			"--only-show-errors",
		]

		completed = subprocess.run(
			command,
			check=False,
			capture_output=True,
			text=True,
		)
		if completed.returncode != 0 or not output_path.is_file():
			return None

		payload = json.loads(output_path.read_text(encoding="utf-8"))
		raw_resources = payload.get("resources", [])
		if not isinstance(raw_resources, list):
			return ArmCompileResult(resources=[], provenance="azure_cli_compile")

		resources = [item for item in raw_resources if isinstance(item, dict)]
		return ArmCompileResult(resources=resources, provenance="azure_cli_compile")

