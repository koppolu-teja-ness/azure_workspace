"""Utilities for discovering Bicep input files for Phase 1.

The discovery agent can be pointed to specific files (`bicep_paths`) and/or
directories (`bicep_directories`) via GraphState.config. This module resolves
those inputs into a deterministic list of existing `.bicep` files.
"""
from __future__ import annotations

from pathlib import Path


def discover_bicep_files(
	bicep_paths: list[str] | None = None,
	bicep_directories: list[str] | None = None,
) -> list[str]:
	"""Return sorted, de-duplicated absolute paths to existing `.bicep` files."""
	files: set[Path] = set()

	for raw_path in bicep_paths or []:
		path = Path(raw_path).expanduser().resolve()
		if path.is_file() and path.suffix.lower() == ".bicep":
			files.add(path)

	for raw_dir in bicep_directories or []:
		directory = Path(raw_dir).expanduser().resolve()
		if directory.is_dir():
			for file_path in directory.rglob("*.bicep"):
				if file_path.is_file():
					files.add(file_path.resolve())

	return [str(path) for path in sorted(files)]
