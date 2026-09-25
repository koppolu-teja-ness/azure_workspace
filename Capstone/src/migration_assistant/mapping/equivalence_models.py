"""Property-level equivalence models used by Phase 1 mapping."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from migration_assistant.graph.state import ResourceType


@dataclass(frozen=True, slots=True)
class PropertyMappingRule:
	azure_property: str
	aws_property: str
	required: bool = False
	notes: tuple[str, ...] = ()


def default_property_mappings_dir() -> Path:
	repo_root = Path(__file__).resolve().parents[3]
	return repo_root / "knowledge_base" / "data" / "property_mappings"


def default_resource_type_mappings_file() -> Path:
	repo_root = Path(__file__).resolve().parents[3]
	return repo_root / "knowledge_base" / "data" / "resource_type_mappings.json"


def load_property_rules(
	mappings_dir: str | None = None,
) -> dict[ResourceType, list[PropertyMappingRule]]:
	directory = Path(mappings_dir) if mappings_dir else default_property_mappings_dir()
	if not directory.is_dir():
		return {}

	rules_by_type: dict[ResourceType, list[PropertyMappingRule]] = {}
	for file_path in directory.glob("*.json"):
		data = json.loads(file_path.read_text(encoding="utf-8"))
		resource_type_value = data.get("azure_resource_type")
		if resource_type_value not in {member.value for member in ResourceType}:
			continue

		resource_type = ResourceType(resource_type_value)
		rule_items = data.get("property_mappings", [])
		rules_by_type[resource_type] = [
			PropertyMappingRule(
				azure_property=item.get("azure_property", ""),
				aws_property=item.get("aws_property", ""),
				required=bool(item.get("required", False)),
				notes=tuple(item.get("notes", [])),
			)
			for item in rule_items
			if item.get("azure_property") and item.get("aws_property")
		]

	return rules_by_type


def load_resource_mapping_types(
	mapping_file_path: str | None = None,
) -> set[ResourceType]:
	path = Path(mapping_file_path) if mapping_file_path else default_resource_type_mappings_file()
	if not path.is_file():
		return set()

	data = json.loads(path.read_text(encoding="utf-8"))
	items = data.get("mappings", [])
	valid_values = {member.value for member in ResourceType}

	result: set[ResourceType] = set()
	for item in items:
		value = item.get("azure_resource_type")
		if value in valid_values:
			result.add(ResourceType(value))
	return result


def missing_property_mapping_coverage(
	mapped_resource_types: set[ResourceType],
	property_rules_by_type: dict[ResourceType, list[PropertyMappingRule]],
) -> set[ResourceType]:
	covered_types = {
		resource_type
		for resource_type, rules in property_rules_by_type.items()
		if rules
	}
	return mapped_resource_types - covered_types
