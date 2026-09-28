"""Shared run store and workflow config validation helpers for API routers."""

from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from pathlib import Path
from threading import Lock
from typing import Any

import psycopg

try:
    from migration_assistant.config.app_config import parse_app_config
    from migration_assistant.graph.checkpoints import (
        get_latest_checkpoint,
        list_checkpoints,
        save_checkpoint,
    )
    from migration_assistant.graph.state import (
        ApprovalDecision,
        GraphState,
        MigrationSpec,
        MigrationStatus,
        graph_state_to_spec,
        spec_to_graph_state,
    )
    from migration_assistant.llm.bedrock_runtime import require_bedrock_settings
except ModuleNotFoundError:
    src_path = Path(__file__).resolve().parents[1] / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from migration_assistant.config.app_config import parse_app_config  # type: ignore[no-redef]
    from migration_assistant.graph.checkpoints import (  # type: ignore[no-redef]
        get_latest_checkpoint,
        list_checkpoints,
        save_checkpoint,
    )
    from migration_assistant.graph.state import (  # type: ignore[no-redef]
        ApprovalDecision,
        GraphState,
        MigrationSpec,
        MigrationStatus,
        graph_state_to_spec,
        spec_to_graph_state,
    )
    from migration_assistant.llm.bedrock_runtime import (  # type: ignore[no-redef]
        require_bedrock_settings,
    )

_LOCK = Lock()
_TABLE_READY = False
_DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/migration_kb"
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS migration_runs (
	run_id TEXT PRIMARY KEY,
	payload JSONB NOT NULL,
	updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def get_run(run_id: str) -> GraphState:
    with _LOCK:
        with _connect() as conn:
            _ensure_table(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT payload FROM migration_runs WHERE run_id = %s",
                    (run_id,),
                )
                row = cur.fetchone()

    if row is None:
        raise KeyError(run_id)

    return _state_from_payload(row[0])


def save_run(state: GraphState) -> None:
    payload = _payload_from_state(state)
    run_id = state["run_id"]
    with _LOCK:
        with _connect() as conn:
            _ensure_table(conn)
            with conn.cursor() as cur:
                cur.execute(
                    """
					INSERT INTO migration_runs (run_id, payload, updated_at)
					VALUES (%s, %s::jsonb, NOW())
					ON CONFLICT (run_id)
					DO UPDATE SET payload = EXCLUDED.payload, updated_at = NOW()
					""",
                    (run_id, json.dumps(payload)),
                )
            conn.commit()


def list_runs() -> list[GraphState]:
    with _LOCK:
        with _connect() as conn:
            _ensure_table(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT payload FROM migration_runs ORDER BY updated_at DESC, run_id ASC"
                )
                rows = cur.fetchall()

    return [_state_from_payload(row[0]) for row in rows]


def save_run_checkpoint(state: GraphState, *, stage: str) -> None:
    with _LOCK:
        with _connect() as conn:
            save_checkpoint(
                conn=conn,
                run_id=state["run_id"],
                stage=stage,
                state=state,
            )


def get_latest_run_checkpoint(run_id: str) -> tuple[str, GraphState] | None:
    with _LOCK:
        with _connect() as conn:
            return get_latest_checkpoint(conn=conn, run_id=run_id)


def list_run_checkpoints(run_id: str) -> list[dict[str, Any]]:
    with _LOCK:
        with _connect() as conn:
            return list_checkpoints(conn=conn, run_id=run_id)


def require_workflow_bedrock_config(config: dict[str, Any]) -> None:
    app_config = parse_app_config(config)
    # Current workflow requires Bedrock for mapping, risk reasoning, and reporting.
    for agent_name in ("mapping_agent", "planning_risk_agent", "reporting_agent"):
        require_bedrock_settings(app_config=app_config, agent_name=agent_name)


def _database_url() -> str:
    return os.getenv("DATABASE_URL", _DEFAULT_DATABASE_URL)


def _connect() -> psycopg.Connection[Any]:
    return psycopg.connect(_database_url())


def _ensure_table(conn: psycopg.Connection[Any]) -> None:
    global _TABLE_READY
    if _TABLE_READY:
        return
    with conn.cursor() as cur:
        cur.execute(_CREATE_TABLE_SQL)
    conn.commit()
    _TABLE_READY = True


def _payload_from_state(state: GraphState) -> dict[str, Any]:
    spec = graph_state_to_spec(state)
    return spec.model_dump(mode="json")


def _state_from_payload(payload: dict[str, Any]) -> GraphState:
    spec = MigrationSpec.model_validate(payload)
    state = spec_to_graph_state(spec)
    return deepcopy(state)


def dump_jsonable_state(state: GraphState) -> dict[str, Any]:
    def _dump_item(item: Any) -> Any:
        if hasattr(item, "model_dump"):
            return item.model_dump(mode="json")
        if isinstance(item, dict):
            return dict(item)
        return item

    return {
        "run_id": state["run_id"],
        "created_at": state["created_at"],
        "source_resources": [_dump_item(item) for item in state.get("source_resources", [])],
        "target_resources": [_dump_item(item) for item in state.get("target_resources", [])],
        "mappings": [item.model_dump(mode="json") for item in state.get("mappings", [])],
        "risk_assessments": [
            item.model_dump(mode="json") for item in state.get("risk_assessments", [])
        ],
        "validation_results": [_dump_item(item) for item in state.get("validation_results", [])],
        "llm_traces": [_dump_item(item) for item in state.get("llm_traces", [])],
        "approval": state.get("approval", ApprovalDecision()).model_dump(mode="json"),
        "status": state.get("status", MigrationStatus.DISCOVERED).value,
        "config": state.get("config", {}),
    }
