"""Minimal Bicep parser for Phase 1.

This parser intentionally focuses on a stable subset:
- resource declarations
- symbolic name
- Azure resource type and api version
- name/location fields
- dependsOn references

It avoids shelling out to Azure CLI so unit tests can run offline.
"""
from __future__ import annotations

import re
from pathlib import Path

from migration_assistant.bicep_parser.models import ParsedBicepResource

RESOURCE_DECLARATION_RE = re.compile(
	r"resource\s+(?P<symbolic>[A-Za-z_][A-Za-z0-9_]*)\s+"
	r"'(?P<resource_type>[^@']+)@(?P<api_version>[^']+)'\s*=\s*\{",
)


def _extract_block(source: str, brace_start_index: int) -> tuple[str, int]:
	"""Extract a `{...}` block from `source` starting at `brace_start_index`."""
	depth = 0
	block_start = brace_start_index
	for index in range(brace_start_index, len(source)):
		char = source[index]
		if char == "{":
			depth += 1
		elif char == "}":
			depth -= 1
			if depth == 0:
				return source[block_start : index + 1], index + 1
	return source[block_start:], len(source)


def _extract_string_value(block_text: str, key: str, default: str = "") -> str:
	pattern = re.compile(rf"\b{re.escape(key)}\s*:\s*'([^']+)'")
	match = pattern.search(block_text)
	if match:
		return match.group(1)
	return default


def _extract_depends_on(block_text: str) -> list[str]:
	depends_match = re.search(r"\bdependsOn\s*:\s*\[(?P<body>.*?)\]", block_text, re.DOTALL)
	if not depends_match:
		return []

	body = depends_match.group("body")
	values: list[str] = []
	for match in re.finditer(r"'([^']+)'|\b([A-Za-z_][A-Za-z0-9_]*)\b", body):
		value = match.group(1) or match.group(2)
		if value not in {"dependsOn"}:
			values.append(value)
	return values


def _extract_top_level_object_keys(object_body: str) -> list[str]:
	keys: list[str] = []
	depth = 0
	cursor = 0
	while cursor < len(object_body):
		char = object_body[cursor]
		if char == "{":
			depth += 1
			cursor += 1
			continue
		if char == "}":
			depth -= 1
			cursor += 1
			continue

		if depth == 0:
			match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", object_body[cursor:])
			if match:
				keys.append(match.group(1))
				cursor += match.end()
				continue

		cursor += 1

	return keys


def _extract_properties(block_text: str) -> dict[str, object]:
	match = re.search(r"\bproperties\s*:\s*\{", block_text)
	if not match:
		return {}

	properties_block, _ = _extract_block(block_text, match.end() - 1)
	inner_body = properties_block[1:-1]
	keys = _extract_top_level_object_keys(inner_body)
	return {key: "__present__" for key in keys}


def parse_bicep_content(content: str) -> list[ParsedBicepResource]:
	"""Parse all supported resource declarations in one Bicep document."""
	resources: list[ParsedBicepResource] = []

	cursor = 0
	while True:
		match = RESOURCE_DECLARATION_RE.search(content, cursor)
		if not match:
			break

		block_text, next_cursor = _extract_block(content, match.end() - 1)
		cursor = next_cursor

		resources.append(
			ParsedBicepResource(
				symbolic_name=match.group("symbolic"),
				resource_type=match.group("resource_type"),
				api_version=match.group("api_version"),
				name=_extract_string_value(
					block_text,
					"name",
					default=match.group("symbolic"),
				),
				location=_extract_string_value(block_text, "location", default="unknown"),
				depends_on=_extract_depends_on(block_text),
				properties=_extract_properties(block_text),
			)
		)

	return resources


def parse_bicep_file(file_path: str) -> list[ParsedBicepResource]:
	"""Parse one Bicep file from disk."""
	path = Path(file_path)
	return parse_bicep_content(path.read_text(encoding="utf-8"))
