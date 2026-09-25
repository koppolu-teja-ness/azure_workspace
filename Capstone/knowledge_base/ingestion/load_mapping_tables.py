"""Loads seed mapping-rule content into the pgvector-backed knowledge base.

Owner: charan (Phase 1 — content). The schema it loads into
(knowledge_base/schema/pgvector_schema.sql) is joint-owned (Phase 0).

Usage:
    python -m knowledge_base.ingestion.load_mapping_tables
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_json_seed(filename: str) -> list[dict[str, Any]]:
    path = DATA_DIR / filename
    if not path.exists():
        logger.warning(
            "Seed file not found (Phase 1 content not written yet): %s", path
        )
        return []
    with path.open() as f:
        return json.load(f)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    # Phase 1 TODO (charan):
    #   1. Populate knowledge_base/data/*.json with real mapping content.
    #   2. Connect to Postgres (DATABASE_URL from .env).
    #   3. Embed each rule's description via the chosen embedding model.
    #   4. Upsert into mapping_rules / rbac_iam_mappings / trigger_mappings /
    #      incompatibilities / region_mappings.
    mapping_rules = load_json_seed("resource_type_mappings.json")
    logger.info(
        "Loaded %d mapping rule seed record(s) (stub — not yet written to DB)",
        len(mapping_rules),
    )


if __name__ == "__main__":
    main()
