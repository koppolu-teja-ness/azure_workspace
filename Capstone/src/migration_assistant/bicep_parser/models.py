"""Data models used by the lightweight Phase 1 Bicep parser."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ParsedBicepResource:
	symbolic_name: str
	resource_type: str
	api_version: str
	name: str
	location: str
	depends_on: list[str] = field(default_factory=list)
	properties: dict[str, object] = field(default_factory=dict)
