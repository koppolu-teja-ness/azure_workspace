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

from knowledge_base.ingestion.embed_and_store import ingest_seed_data

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
    mapping_rules = load_json_seed("resource_type_mappings.json")
    logger.info("Loaded %d mapping rule seed record(s)", len(mapping_rules))

    result = ingest_seed_data(data_dir=DATA_DIR)
    logger.info(
        "KB ingestion complete: %d chunk(s) generated, %d stored",
        result["chunks"],
        result["stored"],
    )


if __name__ == "__main__":
    main()
