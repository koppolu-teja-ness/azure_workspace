"""Source-side migration test suite checks for planning depth and rigor.

This module implements Person A Phase 3 checks:
- schema compatibility
- dependency/referential integrity
- missing-object detection
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from migration_assistant.graph.state import GraphState, graph_state_to_spec


def run_migration_test_suite(state: GraphState) -> dict[str, Any]:
    schema_check = _schema_compatibility_check(state)
    dependency_check = _dependency_integrity_check(state)
    missing_object_check = _missing_object_check(state)

    checks = [schema_check, dependency_check, missing_object_check]
    failed = sum(1 for check in checks if check["status"] == "fail")
    passed = sum(1 for check in checks if check["status"] == "pass")

    return {
        "checks": checks,
        "summary": {
            "total": len(checks),
            "passed": passed,
            "failed": failed,
        },
    }


def _schema_compatibility_check(state: GraphState) -> dict[str, Any]:
    try:
        spec = graph_state_to_spec(state)
        spec.model_dump(mode="json")
        return {
            "name": "schema_compatibility",
            "status": "pass",
            "details": "Graph state can be validated and serialized as MigrationSpec.",
        }
    except Exception as exc:  # pragma: no cover - defensive for malformed runtime states
        return {
            "name": "schema_compatibility",
            "status": "fail",
            "details": f"MigrationSpec validation failed: {exc}",
        }


def _dependency_integrity_check(state: GraphState) -> dict[str, Any]:
    source_resources = state.get("source_resources", [])
    if not source_resources:
        return {
            "name": "dependency_integrity",
            "status": "pass",
            "details": "No source resources present; dependency integrity check skipped.",
            "invalid_dependencies": [],
            "cycles_detected": [],
        }

    by_id = {resource.resource_id: resource for resource in source_resources}
    by_symbol = {
        resource.bicep_symbolic_name: resource.resource_id
        for resource in source_resources
        if resource.bicep_symbolic_name
    }

    invalid_dependencies: list[dict[str, str]] = []
    edges: dict[str, list[str]] = defaultdict(list)
    indegree = {resource.resource_id: 0 for resource in source_resources}

    for resource in source_resources:
        current_id = resource.resource_id
        for dependency in resource.depends_on:
            resolved = by_symbol.get(dependency, dependency)
            if resolved not in by_id:
                invalid_dependencies.append(
                    {
                        "resource_id": current_id,
                        "dependency": dependency,
                    }
                )
                continue
            if resolved == current_id:
                invalid_dependencies.append(
                    {
                        "resource_id": current_id,
                        "dependency": dependency,
                    }
                )
                continue
            edges[resolved].append(current_id)
            indegree[current_id] += 1

    queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    visited_count = 0
    while queue:
        node = queue.popleft()
        visited_count += 1
        for child in edges.get(node, []):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)

    cycles_detected = [
        node for node, degree in indegree.items() if degree > 0
    ]

    status = "pass"
    if invalid_dependencies or cycles_detected:
        status = "fail"

    details = "Dependency graph is valid."
    if status == "fail":
        details = (
            "Dependency integrity issues detected: "
            f"invalid_dependencies={len(invalid_dependencies)}, "
            f"cycles={len(cycles_detected)}"
        )

    return {
        "name": "dependency_integrity",
        "status": status,
        "details": details,
        "invalid_dependencies": invalid_dependencies,
        "cycles_detected": cycles_detected,
    }


def _missing_object_check(state: GraphState) -> dict[str, Any]:
    source_resources = state.get("source_resources", [])
    mappings = state.get("mappings", [])

    source_ids = {resource.resource_id for resource in source_resources}
    mapped_source_ids = {
        mapping.source_resource_id
        for mapping in mappings
        if mapping.target_logical_id
    }
    declared_mapping_source_ids = {mapping.source_resource_id for mapping in mappings}

    missing_source_mappings = sorted(source_ids - mapped_source_ids)
    orphan_mappings = sorted(declared_mapping_source_ids - source_ids)

    status = "pass"
    if missing_source_mappings or orphan_mappings:
        status = "fail"

    details = "All source objects are represented in mappings."
    if status == "fail":
        details = (
            "Missing-object issues detected: "
            f"unmapped_sources={len(missing_source_mappings)}, "
            f"orphan_mappings={len(orphan_mappings)}"
        )

    return {
        "name": "missing_object_detection",
        "status": status,
        "details": details,
        "unmapped_source_resources": missing_source_mappings,
        "orphan_mappings": orphan_mappings,
    }