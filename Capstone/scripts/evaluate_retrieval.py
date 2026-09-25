"""Evaluate retrieval quality for KB-backed mapping rules.

Metrics:
- typed_hit_at_k: expected AWS type appears in top-k when filtered by Azure type,
- semantic_hit_at_k: expected AWS type appears in top-k global semantic search,
- hybrid_top1_accuracy: hybrid retriever chosen mapping matches expected AWS type.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from migration_assistant.graph.state import ResourceType, SourceResource
from migration_assistant.mapping.rag_retriever import RuleBasedMappingRetriever


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate mapping retrieval quality")
    parser.add_argument(
        "--dataset",
        default="knowledge_base/data/resource_type_mappings.json",
        help="Path to mapping dataset JSON",
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("RAG_DATABASE_URL") or os.getenv("DATABASE_URL"),
        help="Postgres URL for vector retrieval",
    )
    parser.add_argument(
        "--embedding-model-id",
        default=os.getenv("RAG_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0"),
        help="Bedrock embedding model id",
    )
    parser.add_argument(
        "--region",
        default=os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION"),
        help="AWS region for Bedrock runtime",
    )
    parser.add_argument("--top-k", type=int, default=3, help="Top-k depth for hit-rate")
    parser.add_argument(
        "--max-distance",
        type=float,
        default=0.40,
        help="Hybrid max cosine distance threshold",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise SystemExit(f"Dataset not found: {dataset_path}")
    if not args.database_url:
        raise SystemExit("DATABASE_URL/RAG_DATABASE_URL is required")

    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    rows = [item for item in data.get("mappings", []) if isinstance(item, dict)]

    retriever = RuleBasedMappingRetriever(
        database_url=args.database_url,
        embedding_model_id=args.embedding_model_id,
        embedding_region_name=args.region,
        top_k=args.top_k,
        max_vector_distance=args.max_distance,
    )

    valid_rows = 0
    typed_hits = 0
    semantic_hits = 0
    hybrid_top1 = 0

    unsupported: list[str] = []

    for item in rows:
        azure_type = str(item.get("azure_resource_type", "")).strip()
        expected_aws_type = str(item.get("aws_resource_type", "")).strip()
        if not azure_type or not expected_aws_type:
            continue

        try:
            resource_type = ResourceType(azure_type)
        except Exception:
            unsupported.append(azure_type)
            continue

        resource = SourceResource(
            resource_id=f"/eval/{resource_type.name.lower()}",
            resource_type=resource_type,
            name=f"eval-{resource_type.name.lower()}",
            api_version="2023-01-01",
            location="eastus",
            properties={},
        )

        embedding = retriever._embed_text(  # noqa: SLF001 - intentional for evaluation
            f"Azure resource type: {azure_type}\nExpected mapping evaluation"
        )
        if not embedding:
            continue

        typed_matches = retriever._query_vector_matches(  # noqa: SLF001
            embedding=embedding,
            azure_resource_type=azure_type,
            top_k=args.top_k,
        )
        semantic_matches = retriever._query_vector_matches(  # noqa: SLF001
            embedding=embedding,
            azure_resource_type=None,
            top_k=args.top_k,
        )

        valid_rows += 1

        if any(match.aws_resource_type == expected_aws_type for match in typed_matches):
            typed_hits += 1
        if any(match.aws_resource_type == expected_aws_type for match in semantic_matches):
            semantic_hits += 1

        selected = retriever.map_resource(resource)
        if selected.mapping_rule_id and selected.target_logical_id:
            if selected.target_logical_id.endswith(expected_aws_type.split("::")[-1]):
                hybrid_top1 += 1

    if valid_rows == 0:
        raise SystemExit("No evaluable rows found (check dataset, DB, and Bedrock access)")

    summary = {
        "dataset": str(dataset_path),
        "samples": valid_rows,
        "top_k": args.top_k,
        "typed_hit_at_k": round(typed_hits / valid_rows, 4),
        "semantic_hit_at_k": round(semantic_hits / valid_rows, 4),
        "hybrid_top1_accuracy": round(hybrid_top1 / valid_rows, 4),
        "unsupported_resource_types": sorted(set(unsupported)),
    }
    json.dump(summary, fp=sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()