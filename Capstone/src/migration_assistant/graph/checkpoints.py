"""Postgres-backed checkpoint persistence for GraphState snapshots."""

from __future__ import annotations

import json
from typing import Any

import psycopg

from migration_assistant.graph.state import GraphState, MigrationSpec, spec_to_graph_state

_CREATE_CHECKPOINTS_SQL = """
CREATE TABLE IF NOT EXISTS migration_checkpoints (
  id BIGSERIAL PRIMARY KEY,
  run_id TEXT NOT NULL,
  stage TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_migration_checkpoints_run_id_created_at
ON migration_checkpoints (run_id, created_at DESC);
"""


def ensure_checkpoint_table(conn: psycopg.Connection[Any]) -> None:
    with conn.cursor() as cur:
        cur.execute(_CREATE_CHECKPOINTS_SQL)
    conn.commit()


def save_checkpoint(
    *,
    conn: psycopg.Connection[Any],
    run_id: str,
    stage: str,
    state: GraphState,
) -> None:
    ensure_checkpoint_table(conn)
    payload = MigrationSpec.model_validate(
        {
            **state,
            "run_id": state["run_id"],
            "created_at": state["created_at"],
        }
    ).model_dump(mode="json")

    with conn.cursor() as cur:
        cur.execute(
            """
			INSERT INTO migration_checkpoints (run_id, stage, payload)
			VALUES (%s, %s, %s::jsonb)
			""",
            (run_id, stage, json.dumps(payload)),
        )
    conn.commit()


def get_latest_checkpoint(
    *,
    conn: psycopg.Connection[Any],
    run_id: str,
) -> tuple[str, GraphState] | None:
    ensure_checkpoint_table(conn)
    with conn.cursor() as cur:
        cur.execute(
            """
			SELECT stage, payload
			FROM migration_checkpoints
			WHERE run_id = %s
			ORDER BY created_at DESC, id DESC
			LIMIT 1
			""",
            (run_id,),
        )
        row = cur.fetchone()

    if row is None:
        return None

    stage = str(row[0])
    payload = row[1]
    spec = MigrationSpec.model_validate(payload)
    return stage, spec_to_graph_state(spec)


def list_checkpoints(*, conn: psycopg.Connection[Any], run_id: str) -> list[dict[str, Any]]:
    ensure_checkpoint_table(conn)
    with conn.cursor() as cur:
        cur.execute(
            """
			SELECT id, stage, created_at
			FROM migration_checkpoints
			WHERE run_id = %s
			ORDER BY created_at ASC, id ASC
			""",
            (run_id,),
        )
        rows = cur.fetchall()

    return [
        {
            "id": int(row[0]),
            "stage": str(row[1]),
            "created_at": row[2].isoformat() if hasattr(row[2], "isoformat") else str(row[2]),
        }
        for row in rows
    ]
