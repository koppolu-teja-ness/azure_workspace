"""Seed knowledge-base tables with chunked embeddings."""
from __future__ import annotations

from knowledge_base.ingestion.embed_and_store import ingest_seed_data


def main() -> None:
	result = ingest_seed_data()
	print(
		"KB seed complete: "
		f"generated={result['chunks']} chunk(s), stored={result['stored']} row(s)"
	)


if __name__ == "__main__":
	main()
