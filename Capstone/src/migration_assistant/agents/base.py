"""Shared agent interface. Every agent module (discovery_agent.py,
mapping_agent.py, etc.) exposes a module-level `run(state: GraphState) ->
dict` function with this signature — that's the only contract LangGraph
needs, and it's deliberately looser than a class hierarchy so either of you
can stub, test, and swap implementations without touching workflow.py.

If you'd rather implement an agent as a class (e.g. because it holds an LLM
client or RAG retriever as state), subclass BaseAgent and expose a
module-level `run` as a thin wrapper — see mapping_agent.py for an example
of that pattern.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from migration_assistant.graph.state import GraphState


class BaseAgent(ABC):
    name: str = "base_agent"

    @abstractmethod
    def run(self, state: GraphState) -> dict[str, Any]:
        """Return a partial state update, not the full state."""
        raise NotImplementedError

    def __call__(self, state: GraphState) -> dict[str, Any]:
        return self.run(state)
