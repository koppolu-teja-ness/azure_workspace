"""Property equivalence models and JSON loading helpers."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from migration_assistant.graph.state import ResourceType


@dataclass(frozen=True, slots=True)
class PropertyMappingRule:
	azure_resource_type: ResourceType
	azure_property: str
	aws_property: str


def load_property_rules(
	property_mappings_dir: str | None = None,
) -> dict[ResourceType, list[PropertyMappingRule]]:
	path = Path(property_mappings_dir) if property_mappings_dir else _default_property_mappings_dir()
	if not path.is_dir():
		return {}

	results: dict[ResourceType, list[PropertyMappingRule]] = {}
	supported_values = {member.value: member for member in ResourceType}

	for file_path in sorted(path.glob("*.json")):
		payload = json.loads(file_path.read_text(encoding="utf-8"))
		resource_type_value = payload.get("azure_resource_type")
		resource_type = supported_values.get(resource_type_value)
		if resource_type is None:
			continue

		raw_rules = payload.get("property_mappings", [])
		if not isinstance(raw_rules, list):
			continue

		rules_for_type: list[PropertyMappingRule] = []
		for item in raw_rules:
			if not isinstance(item, dict):
				continue
			azure_property = item.get("azure_property")
			aws_property = item.get("aws_property")
			if not isinstance(azure_property, str) or not azure_property.strip():
				continue
			if not isinstance(aws_property, str) or not aws_property.strip():
				continue
			rules_for_type.append(
				PropertyMappingRule(
					azure_resource_type=resource_type,
					azure_property=azure_property.strip(),
					aws_property=aws_property.strip(),
				)
			)

		if rules_for_type:
			results[resource_type] = rules_for_type

	return results


def load_resource_mapping_types(
	mapping_file_path: str | None = None,
) -> set[ResourceType]:
	path = Path(mapping_file_path) if mapping_file_path else _default_mapping_file_path()
	if not path.is_file():
		return set()

	payload = json.loads(path.read_text(encoding="utf-8"))
	mappings = payload.get("mappings", [])
	if not isinstance(mappings, list):
		return set()

	supported_values = {member.value: member for member in ResourceType}
	resource_types: set[ResourceType] = set()

	for item in mappings:
		if not isinstance(item, dict):
			continue
		value = item.get("azure_resource_type")
		resource_type = supported_values.get(value)
		if resource_type is not None:
			resource_types.add(resource_type)

	return resource_types


def missing_property_mapping_coverage(
	mapped_types: set[ResourceType],
	property_rules: dict[ResourceType, list[PropertyMappingRule]],
) -> set[ResourceType]:
	missing: set[ResourceType] = set()
	for resource_type in mapped_types:
		rules = property_rules.get(resource_type, [])
		if not rules:
			missing.add(resource_type)
	return missing


def _default_property_mappings_dir() -> Path:
	repo_root = Path(__file__).resolve().parents[3]
	return repo_root / "knowledge_base" / "data" / "property_mappings"


def _default_mapping_file_path() -> Path:
	repo_root = Path(__file__).resolve().parents[3]
	return repo_root / "knowledge_base" / "data" / "resource_type_mappings.json"
