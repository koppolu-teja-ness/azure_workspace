"""Observability wiring helpers for LangSmith/LangFuse tracing."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TracingConfig:
	enabled: bool
	project: str
	provider: str
	endpoint: str | None

	def to_env(self) -> dict[str, str]:
		env = {
			"LANGCHAIN_TRACING_V2": "true" if self.enabled else "false",
			"LANGCHAIN_PROJECT": self.project,
		}
		if self.endpoint:
			env["LANGCHAIN_ENDPOINT"] = self.endpoint
		return env


def build_tracing_config(config: dict[str, Any] | None = None) -> TracingConfig:
	raw = config or {}
	observability = raw.get("observability", {}) if isinstance(raw, dict) else {}
	if not isinstance(observability, dict):
		observability = {}

	tracing = observability.get("tracing", {})
	if not isinstance(tracing, dict):
		tracing = {}

	enabled = bool(tracing.get("enabled", False))
	provider = str(tracing.get("provider", "langsmith")).strip() or "langsmith"
	project = str(tracing.get("project", "azure-aws-migration-assistant")).strip()
	endpoint_value = tracing.get("endpoint")
	endpoint = str(endpoint_value).strip() if isinstance(endpoint_value, str) else None
	if endpoint == "":
		endpoint = None

	return TracingConfig(
		enabled=enabled,
		project=project,
		provider=provider,
		endpoint=endpoint,
	)
