"""Function App-specific mapping heuristics."""

from __future__ import annotations

from migration_assistant.graph.state import SourceResource


def apply(
    resource: SourceResource,
    *,
    confidence: float,
    notes: tuple[str, ...],
) -> tuple[float, tuple[str, ...]]:
    updated = confidence
    appended: list[str] = []
    properties = resource.properties

    kind = properties.get("kind")
    if isinstance(kind, str) and "functionapp" in kind.lower():
        appended.append("Function App maps to Lambda runtime and event source configuration.")

    https_only = properties.get("httpsOnly")
    if https_only is False:
        updated -= 0.03
        appended.append(
            "Source allows HTTP; enforce HTTPS-only behavior in API Gateway/Lambda path."
        )

    site_config = properties.get("siteConfig")
    if isinstance(site_config, dict):
        if site_config.get("alwaysOn") is True:
            updated -= 0.03
            appended.append(
                "Azure alwaysOn has no direct Lambda equivalent; review cold-start impact."
            )
        if site_config.get("functionTimeout") is not None:
            appended.append("Validate function timeout translation against Lambda limits.")

    updated = max(0.0, min(1.0, updated))
    if not appended:
        return updated, notes
    return updated, tuple(dict.fromkeys([*notes, *appended]))
