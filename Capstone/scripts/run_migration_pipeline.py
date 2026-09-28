"""CLI entrypoint for a full migration run. Wraps the compiled LangGraph
graph from graph/workflow.py with basic argument handling.

Usage:
    python scripts/run_migration_pipeline.py --run-id demo-001
"""

from __future__ import annotations

import argparse
import logging
import os
from datetime import UTC, datetime

from migration_assistant.graph.state import GraphState, MigrationStatus
from migration_assistant.graph.workflow import build_graph


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the migration pipeline")
    parser.add_argument("--run-id", default="local-run")
    parser.add_argument(
        "--bicep",
        action="append",
        default=[],
        help="Path to a Bicep file (can be repeated).",
    )
    parser.add_argument(
        "--bicep-dir",
        action="append",
        default=[],
        help="Directory to recursively scan for .bicep files (can be repeated).",
    )
    parser.add_argument(
        "--bedrock-model-id",
        default=os.getenv("BEDROCK_MODEL_ID", "").strip(),
        help="Bedrock model id (or set BEDROCK_MODEL_ID env var).",
    )
    parser.add_argument(
        "--bedrock-region",
        default=os.getenv("BEDROCK_REGION", os.getenv("AWS_REGION", "us-east-1")),
        help="Bedrock region name.",
    )
    parser.add_argument(
        "--bedrock-temperature",
        type=float,
        default=0.7,
        help="Bedrock generation temperature.",
    )
    parser.add_argument(
        "--bedrock-max-tokens",
        type=int,
        default=800,
        help="Bedrock max output tokens.",
    )
    args = parser.parse_args()

    if not args.bedrock_model_id:
        parser.error(
            "Bedrock model id is required. Provide --bedrock-model-id or BEDROCK_MODEL_ID."
        )

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
        "config": {
            "bicep_paths": args.bicep,
            "bicep_directories": args.bicep_dir,
            "llm": {
                "enabled": True,
                "provider": "aws_bedrock",
                "bedrock": {
                    "model_id": args.bedrock_model_id,
                    "region_name": args.bedrock_region,
                    "temperature": float(args.bedrock_temperature),
                    "max_tokens": int(args.bedrock_max_tokens),
                },
            },
        },
    }

    final_state = app.invoke(initial_state)
    print(f"Run {args.run_id} finished with status: {final_state['status']}")


if __name__ == "__main__":
    main()
