"""Embedding + pgvector ingestion pipeline for knowledge-base seed content."""
from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
from typing import Any

try:
	import boto3
except Exception:  # pragma: no cover - optional until ingestion is executed
	boto3 = None

try:
	import psycopg
except Exception:  # pragma: no cover - optional until ingestion is executed
	psycopg = None

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class IngestionSettings:
	database_url: str
	embedding_model_id: str
	aws_region: str | None
	chunk_size_chars: int = 900
	chunk_overlap_chars: int = 150


@dataclass(frozen=True, slots=True)
class KBChunk:
	table: str
	key: str
	text: str
	metadata: dict[str, Any]


def load_ingestion_settings() -> IngestionSettings:
	database_url = os.getenv("RAG_DATABASE_URL") or os.getenv("DATABASE_URL")
	if not database_url:
		raise ValueError("DATABASE_URL or RAG_DATABASE_URL is required for KB ingestion")

	return IngestionSettings(
		database_url=database_url,
		embedding_model_id=os.getenv(
			"RAG_EMBEDDING_MODEL_ID",
			"amazon.titan-embed-text-v2:0",
		),
		aws_region=os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION"),
		chunk_size_chars=int(os.getenv("RAG_CHUNK_SIZE", "900")),
		chunk_overlap_chars=int(os.getenv("RAG_CHUNK_OVERLAP", "150")),
	)


def ingest_seed_data(*, data_dir: Path | None = None) -> dict[str, int]:
	if boto3 is None:
		raise RuntimeError("boto3 is required for embedding ingestion")
	if psycopg is None:
		raise RuntimeError("psycopg is required for pgvector ingestion")

	settings = load_ingestion_settings()
	base_dir = data_dir or Path(__file__).resolve().parent.parent / "data"
	chunks = _build_chunks_from_seed_data(
		base_dir,
		chunk_size_chars=settings.chunk_size_chars,
		chunk_overlap_chars=settings.chunk_overlap_chars,
	)

	if not chunks:
		logger.warning("No chunks were produced from seed files at %s", base_dir)
		return {"chunks": 0, "stored": 0}

	runtime = boto3.client("bedrock-runtime", region_name=settings.aws_region)
	stored = 0

	with psycopg.connect(settings.database_url) as conn:
		with conn.cursor() as cur:
			for chunk in chunks:
				embedding = _embed_text(
					runtime_client=runtime,
					model_id=settings.embedding_model_id,
					text=chunk.text,
				)
				if not embedding:
					continue

				_upsert_chunk(cur, chunk=chunk, embedding=embedding)
				stored += 1

		conn.commit()

	logger.info("Stored %d embedded chunk(s) into pgvector KB", stored)
	return {"chunks": len(chunks), "stored": stored}


def _build_chunks_from_seed_data(
	data_dir: Path,
	*,
	chunk_size_chars: int,
	chunk_overlap_chars: int,
) -> list[KBChunk]:
	chunks: list[KBChunk] = []

	resource_mapping_file = data_dir / "resource_type_mappings.json"
	resource_data = _read_json(resource_mapping_file)
	for item in resource_data.get("mappings", []):
		if not isinstance(item, dict):
			continue

		key = str(item.get("mapping_rule_id") or item.get("azure_resource_type") or "")
		if not key:
			continue

		text = (
			f"Azure resource type: {item.get('azure_resource_type', '')}\n"
			f"AWS resource type: {item.get('aws_resource_type', '')}\n"
			f"Notes: {' '.join(item.get('notes', []))}"
		)
		for index, piece in enumerate(_chunk_text(text, chunk_size_chars, chunk_overlap_chars)):
			chunks.append(
				KBChunk(
					table="mapping_rules",
					key=f"{key}:{index}",
					text=piece,
					metadata={
						"azure_resource_type": item.get("azure_resource_type", ""),
						"aws_resource_type": item.get("aws_resource_type", ""),
						"property_mapping": {},
						"description": piece,
						"source": "knowledge_base/data/resource_type_mappings.json",
					},
				)
			)

	property_mappings_dir = data_dir / "property_mappings"
	if property_mappings_dir.is_dir():
		for property_file in property_mappings_dir.glob("*.json"):
			data = _read_json(property_file)
			azure_type = str(data.get("azure_resource_type", ""))
			for item in data.get("property_mappings", []):
				if not isinstance(item, dict):
					continue
				az_prop = str(item.get("azure_property", ""))
				aws_prop = str(item.get("aws_property", ""))
				if not az_prop or not aws_prop:
					continue

				notes = " ".join(item.get("notes", []))
				text = (
					f"Azure resource type: {azure_type}\n"
					f"Azure property: {az_prop}\n"
					f"AWS property: {aws_prop}\n"
					f"Required: {bool(item.get('required', False))}\n"
					f"Notes: {notes}"
				)
				for index, piece in enumerate(
					_chunk_text(text, chunk_size_chars, chunk_overlap_chars)
				):
					chunks.append(
						KBChunk(
							table="mapping_rules",
							key=f"{azure_type}:{az_prop}:{index}",
							text=piece,
							metadata={
								"azure_resource_type": azure_type,
								"aws_resource_type": "",
								"property_mapping": {
									"azure_property": az_prop,
									"aws_property": aws_prop,
									"required": bool(item.get("required", False)),
								},
								"description": piece,
								"source": f"knowledge_base/data/property_mappings/{property_file.name}",
							},
						)
					)

	rbac_data = _read_json(data_dir / "rbac_to_iam_rules.json")
	for item in rbac_data.get("rules", []):
		if not isinstance(item, dict):
			continue
		azure_role = str(item.get("azure_role", "")).strip()
		aws_policy = str(item.get("aws_managed_policy", "")).strip()
		if not azure_role or not aws_policy:
			continue
		text = (
			f"Azure RBAC role: {azure_role}\n"
			f"AWS managed policy: {aws_policy}\n"
			f"Notes: {' '.join(item.get('notes', []))}"
		)
		chunks.append(
			KBChunk(
				table="rbac_iam_mappings",
				key=azure_role,
				text=text,
				metadata={
					"azure_rbac_role": azure_role,
					"iam_policy_json": {"managed_policy": aws_policy},
					"notes": text,
				},
			)
		)

	trigger_data = _read_json(data_dir / "trigger_mappings.json")
	for item in trigger_data.get("mappings", []):
		if not isinstance(item, dict):
			continue
		azure_trigger = str(item.get("azure_trigger", "")).strip()
		aws_trigger = str(item.get("aws_trigger", "")).strip()
		if not azure_trigger or not aws_trigger:
			continue
		text = (
			f"Azure trigger: {azure_trigger}\n"
			f"AWS equivalent: {aws_trigger}\n"
			f"Notes: {' '.join(item.get('notes', []))}"
		)
		chunks.append(
			KBChunk(
				table="trigger_mappings",
				key=azure_trigger,
				text=text,
				metadata={
					"azure_trigger_type": azure_trigger,
					"aws_equivalent": aws_trigger,
					"config_template": {},
				},
			)
		)

	incompatibility_file = data_dir / "known_incompatibilities.md"
	if incompatibility_file.exists():
		markdown = incompatibility_file.read_text(encoding="utf-8")
		for index, piece in enumerate(_chunk_text(markdown, chunk_size_chars, chunk_overlap_chars)):
			if not piece.strip():
				continue
			chunks.append(
				KBChunk(
					table="incompatibilities",
					key=f"known-incompatibilities:{index}",
					text=piece,
					metadata={
						"azure_concept": "unknown",
						"aws_concept": "unknown",
						"description": piece,
						"workaround": "",
					},
				)
			)

	return chunks


def _chunk_text(text: str, chunk_size_chars: int, chunk_overlap_chars: int) -> list[str]:
	normalized = " ".join(text.split())
	if not normalized:
		return []

	chunk_size_chars = max(200, chunk_size_chars)
	chunk_overlap_chars = max(0, min(chunk_overlap_chars, chunk_size_chars // 2))

	chunks: list[str] = []
	start = 0
	text_len = len(normalized)

	while start < text_len:
		end = min(text_len, start + chunk_size_chars)
		chunk = normalized[start:end].strip()
		if chunk:
			chunks.append(chunk)
		if end >= text_len:
			break
		start = end - chunk_overlap_chars

	return chunks


def _embed_text(*, runtime_client: Any, model_id: str, text: str) -> list[float]:
	payload = json.dumps({"inputText": text})
	response = runtime_client.invoke_model(
		modelId=model_id,
		contentType="application/json",
		accept="application/json",
		body=payload,
	)
	body = response.get("body")
	data = json.loads(body.read().decode("utf-8") if body else "{}")
	embedding = data.get("embedding", [])
	return [float(value) for value in embedding]


def _upsert_chunk(cur: Any, *, chunk: KBChunk, embedding: list[float]) -> None:
	vector_literal = _to_pgvector_literal(embedding)

	if chunk.table == "mapping_rules":
		azure_type = str(chunk.metadata.get("azure_resource_type", ""))
		aws_type = str(chunk.metadata.get("aws_resource_type", ""))
		property_mapping = chunk.metadata.get("property_mapping", {})
		description = str(chunk.metadata.get("description", ""))
		source = str(chunk.metadata.get("source", "seed"))

		cur.execute(
			"""
			UPDATE mapping_rules
			SET property_mapping = %s::jsonb,
				description = %s,
				source = %s,
				embedding = %s::vector,
				updated_at = now()
			WHERE azure_resource_type = %s
			  AND aws_resource_type = %s
			""",
			(
				json.dumps(property_mapping),
				description,
				source,
				vector_literal,
				azure_type,
				aws_type,
			),
		)
		if cur.rowcount == 0:
			cur.execute(
				"""
				INSERT INTO mapping_rules (
					azure_resource_type,
					aws_resource_type,
					property_mapping,
					description,
					source,
					embedding
				) VALUES (%s, %s, %s::jsonb, %s, %s, %s::vector)
				""",
				(
					azure_type,
					aws_type,
					json.dumps(property_mapping),
					description,
					source,
					vector_literal,
				),
			)
		return

	if chunk.table == "rbac_iam_mappings":
		azure_role = str(chunk.metadata.get("azure_rbac_role", ""))
		iam_policy_json = chunk.metadata.get("iam_policy_json", {})
		notes = str(chunk.metadata.get("notes", ""))
		cur.execute(
			"""
			UPDATE rbac_iam_mappings
			SET iam_policy_json = %s::jsonb,
				notes = %s,
				embedding = %s::vector
			WHERE azure_rbac_role = %s
			""",
			(json.dumps(iam_policy_json), notes, vector_literal, azure_role),
		)
		if cur.rowcount == 0:
			cur.execute(
				"""
				INSERT INTO rbac_iam_mappings (
					azure_rbac_role,
					iam_policy_json,
					notes,
					embedding
				) VALUES (%s, %s::jsonb, %s, %s::vector)
				""",
				(azure_role, json.dumps(iam_policy_json), notes, vector_literal),
			)
		return

	if chunk.table == "trigger_mappings":
		azure_trigger_type = str(chunk.metadata.get("azure_trigger_type", ""))
		aws_equivalent = str(chunk.metadata.get("aws_equivalent", ""))
		config_template = chunk.metadata.get("config_template", {})
		cur.execute(
			"""
			UPDATE trigger_mappings
			SET aws_equivalent = %s,
				config_template = %s::jsonb,
				embedding = %s::vector
			WHERE azure_trigger_type = %s
			""",
			(
				aws_equivalent,
				json.dumps(config_template),
				vector_literal,
				azure_trigger_type,
			),
		)
		if cur.rowcount == 0:
			cur.execute(
				"""
				INSERT INTO trigger_mappings (
					azure_trigger_type,
					aws_equivalent,
					config_template,
					embedding
				) VALUES (%s, %s, %s::jsonb, %s::vector)
				""",
				(
					azure_trigger_type,
					aws_equivalent,
					json.dumps(config_template),
					vector_literal,
				),
			)
		return

	if chunk.table == "incompatibilities":
		description = str(chunk.metadata.get("description", ""))
		workaround = str(chunk.metadata.get("workaround", ""))
		azure_concept = str(chunk.metadata.get("azure_concept", "unknown"))
		aws_concept = str(chunk.metadata.get("aws_concept", "unknown"))

		cur.execute(
			"""
			UPDATE incompatibilities
			SET workaround = %s,
				embedding = %s::vector
			WHERE azure_concept = %s
			  AND aws_concept = %s
			  AND description = %s
			""",
			(
				workaround,
				vector_literal,
				azure_concept,
				aws_concept,
				description,
			),
		)
		if cur.rowcount == 0:
			cur.execute(
				"""
				INSERT INTO incompatibilities (
					azure_concept,
					aws_concept,
					description,
					workaround,
					embedding
				) VALUES (%s, %s, %s, %s, %s::vector)
				""",
				(azure_concept, aws_concept, description, workaround, vector_literal),
			)


def _to_pgvector_literal(values: list[float]) -> str:
	return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


def _read_json(path: Path) -> dict[str, Any]:
	if not path.exists():
		logger.warning("Seed file missing: %s", path)
		return {}
	return json.loads(path.read_text(encoding="utf-8"))
