"""Conversion helpers between parser output and graph contract models."""
from __future__ import annotations

from migration_assistant.bicep_parser.models import ParsedBicepResource
from migration_assistant.graph.state import ResourceType, SourceResource


def to_source_resources(
	parsed_resources: list[ParsedBicepResource],
	run_id: str,
) -> list[SourceResource]:
	"""Convert parsed resources into SourceResource entries.

	Unknown/unsupported Azure resource types are skipped because the shared
	contract uses an enum constrained to supported types.
	"""
	source_resources: list[SourceResource] = []
	supported_values = {resource_type.value for resource_type in ResourceType}

	for item in parsed_resources:
		if item.resource_type not in supported_values:
			continue

		resource_type = ResourceType(item.resource_type)
		resource_id = (
			f"/migration-runs/{run_id}/providers/{item.resource_type}/"
			f"{item.name}"
		)
		source_resources.append(
			SourceResource(
				resource_id=resource_id,
				resource_type=resource_type,
				name=item.name,
				bicep_symbolic_name=item.symbolic_name,
				api_version=item.api_version,
				location=item.location,
				properties=dict(item.properties),
				depends_on=list(item.depends_on),
			)
		)

	return source_resources
