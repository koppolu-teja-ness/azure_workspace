"""CLI entrypoint for a full migration run. Wraps the compiled LangGraph
graph from graph/workflow.py with basic argument handling.

Usage:
    python scripts/run_migration_pipeline.py --run-id demo-001
"""
from __future__ import annotations

import argparse
import logging
from datetime import UTC, datetime

from migration_assistant.graph.state import GraphState, MigrationStatus
from migration_assistant.graph.workflow import build_graph


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the migration pipeline")
    parser.add_argument("--run-id", default="local-run")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    app = build_graph()
    initial_state: GraphState = {
        "run_id": args.run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "source_resources": [],
        "target_resources": [],
        "mappings": [],
        "risk_assessments": [],
        "validation_results": [],
        "status": MigrationStatus.DISCOVERED,
        "config": {},
    }

    final_state = app.invoke(initial_state)
    print(f"Run {args.run_id} finished with status: {final_state['status']}")


if __name__ == "__main__":
    main()
