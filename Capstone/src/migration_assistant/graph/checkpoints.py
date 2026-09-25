"""Per-resource deployment checkpoint tracking.

Filled in during Phase 2/3 (owner: saurav) alongside the Deployment Agent.
Defining the shape now, in Phase 0, so the reporting agent and Migration
Spec can reference it without blocking on Person B's later work.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class CheckpointStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ResourceCheckpoint(BaseModel):
    resource_id: str
    status: CheckpointStatus = CheckpointStatus.PENDING
    attempt: int = 0
    error: str | None = None


class DeploymentCheckpoints(BaseModel):
    run_id: str
    checkpoints: dict[str, ResourceCheckpoint] = {}

    def mark(
        self, resource_id: str, status: CheckpointStatus, error: str | None = None
    ) -> None:
        self.checkpoints[resource_id] = ResourceCheckpoint(
            resource_id=resource_id, status=status, error=error
        )
