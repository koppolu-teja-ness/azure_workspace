"""Shared agent interfaces for the Phase 0 pipeline contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

AgentStatus = Literal["success", "error", "skipped"]
AgentName = Literal[
    "discovery",
    "parser_analyzer",
    "mapping",
    "cfn_generator",
    "static_validation",
    "reporting",
]


class AgentInput(BaseModel):
    """Common input shape all pipeline agents receive."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    spec_version: str = "1.0.0"
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    """Common output shape all pipeline agents emit."""

    model_config = ConfigDict(extra="forbid")

    agent_name: AgentName
    status: AgentStatus
    payload: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class SharedAgent(Protocol):
    """Protocol for strongly typed shared pipeline agent implementations."""

    agent_name: AgentName

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """Execute the agent with a shared contract."""


class AbstractAgent(ABC):
    """Base class for concrete agents with helper success/error constructors."""

    agent_name: AgentName

    @abstractmethod
    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """Execute agent and return structured output."""

    def success(
        self,
        payload: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
    ) -> AgentOutput:
        return AgentOutput(
            agent_name=self.agent_name,
            status="success",
            payload=payload or {},
            warnings=warnings or [],
        )

    def error(self, message: str) -> AgentOutput:
        return AgentOutput(
            agent_name=self.agent_name,
            status="error",
            errors=[message],
        )
