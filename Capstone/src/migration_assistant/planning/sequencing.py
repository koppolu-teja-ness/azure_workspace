"""Simple dependency-aware ordering utilities."""
from __future__ import annotations

from collections import defaultdict, deque

from migration_assistant.graph.state import SourceResource


def order_resources(resources: list[SourceResource]) -> list[SourceResource]:
	"""Return resources in a dependency-friendly order.

	Dependencies are interpreted primarily via symbolic names; unresolved
	dependencies are ignored so planning remains robust for partial inputs.
	"""
	by_symbol = {
		resource.bicep_symbolic_name: resource
		for resource in resources
		if resource.bicep_symbolic_name
	}
	indegree: dict[str, int] = {
		symbol: 0
		for symbol in by_symbol
	}
	edges: dict[str, list[str]] = defaultdict(list)

	for resource in resources:
		symbol = resource.bicep_symbolic_name
		if not symbol:
			continue
		for dependency in resource.depends_on:
			if dependency in by_symbol:
				edges[dependency].append(symbol)
				indegree[symbol] += 1

	queue = deque(sorted(symbol for symbol, degree in indegree.items() if degree == 0))
	ordered_symbols: list[str] = []

	while queue:
		symbol = queue.popleft()
		ordered_symbols.append(symbol)
		for child in sorted(edges.get(symbol, [])):
			indegree[child] -= 1
			if indegree[child] == 0:
				queue.append(child)

	ordered = [by_symbol[symbol] for symbol in ordered_symbols]

	# Preserve resources without symbolic names and cycle leftovers.
	seen_ids = {resource.resource_id for resource in ordered}
	for resource in resources:
		if resource.resource_id not in seen_ids:
			ordered.append(resource)

	return ordered
