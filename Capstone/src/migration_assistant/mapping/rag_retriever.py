"""Hybrid mapping retriever with deterministic fallback.

This module supports three retrieval paths:
1) deterministic JSON-backed mapping rules (always available),
2) pgvector cosine retrieval from Postgres (when configured), and
3) a hybrid mode that tries exact type-filtered vector hits before fallback.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
from typing import Any

try:
	import boto3
except Exception:  # pragma: no cover - optional dependency in local dev
	boto3 = None

try:
	import psycopg
except Exception:  # pragma: no cover - optional dependency in local dev
	psycopg = None

from migration_assistant.graph.state import MappingRecord, ResourceType, SourceResource
from migration_assistant.mapping.equivalence_models import load_property_rules

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class MappingRule:
	rule_id: str
	aws_resource_type: str
	confidence: float
	notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class VectorMatch:
	rule_id: str
	aws_resource_type: str
	confidence: float
	distance: float
	notes: tuple[str, ...] = ()


DEFAULT_RULES: dict[ResourceType, MappingRule] = {
	ResourceType.KEY_VAULT: MappingRule(
		rule_id="rule-keyvault-secretsmanager",
		aws_resource_type="AWS::SecretsManager::Secret",
		confidence=0.9,
		notes=("Key Vault maps to Secrets Manager for secret storage.",),
	),
	ResourceType.FUNCTION_APP: MappingRule(
		rule_id="rule-functionapp-lambda",
		aws_resource_type="AWS::Lambda::Function",
		confidence=0.88,
		notes=("Function App compute maps to Lambda.",),
	),
	ResourceType.VNET: MappingRule(
		rule_id="rule-vnet-vpc",
		aws_resource_type="AWS::EC2::VPC",
		confidence=0.92,
		notes=("Virtual Network maps to VPC.",),
	),
	ResourceType.SUBNET: MappingRule(
		rule_id="rule-subnet-subnet",
		aws_resource_type="AWS::EC2::Subnet",
		confidence=0.92,
	),
	ResourceType.NSG: MappingRule(
		rule_id="rule-nsg-securitygroup",
		aws_resource_type="AWS::EC2::SecurityGroup",
		confidence=0.87,
	),
	ResourceType.PRIVATE_ENDPOINT: MappingRule(
		rule_id="rule-privateendpoint-privatelink",
		aws_resource_type="AWS::EC2::VPCEndpoint",
		confidence=0.8,
	),
}


class RuleBasedMappingRetriever:
	def __init__(
		self,
		rules: dict[ResourceType, MappingRule] | None = None,
		mapping_file_path: str | None = None,
		property_mappings_dir: str | None = None,
		database_url: str | None = None,
		embedding_model_id: str | None = None,
		embedding_region_name: str | None = None,
		top_k: int = 3,
		max_vector_distance: float = 0.40,
	) -> None:
		if rules is not None:
			self._rules = rules
		else:
			loaded_rules = _load_rules_from_json(mapping_file_path)
			self._rules = loaded_rules or DEFAULT_RULES

		self._property_rules = load_property_rules(property_mappings_dir)
		self._database_url = database_url or os.getenv("RAG_DATABASE_URL") or os.getenv(
			"DATABASE_URL"
		)
		self._embedding_model_id = embedding_model_id or os.getenv(
			"RAG_EMBEDDING_MODEL_ID",
			"amazon.titan-embed-text-v2:0",
		)
		self._embedding_region_name = embedding_region_name or os.getenv(
			"AWS_REGION"
		) or os.getenv("AWS_DEFAULT_REGION")
		self._top_k = max(1, int(top_k))
		self._max_vector_distance = max(0.0, float(max_vector_distance))
		self._bedrock_runtime_client: Any | None = None

	def map_resource(self, resource: SourceResource) -> MappingRecord:
		deterministic_rule = self._rules.get(resource.resource_type)
		selected_rule = deterministic_rule
		vector_match = self._hybrid_vector_lookup(resource)
		if vector_match is not None:
			selected_rule = MappingRule(
				rule_id=vector_match.rule_id,
				aws_resource_type=vector_match.aws_resource_type,
				confidence=vector_match.confidence,
				notes=vector_match.notes,
			)

		if not selected_rule:
			return MappingRecord(
				source_resource_id=resource.resource_id,
				confidence=0.0,
				notes=["No mapping rule found for resource type."],
				unmapped_properties=["*"],
			)

		logical_id = _build_logical_id(resource.name, selected_rule.aws_resource_type)
		property_rules = self._property_rules.get(resource.resource_type, [])
		mapped_properties = {item.azure_property for item in property_rules}
		source_property_keys = set(resource.properties.keys())
		unmapped_properties = sorted(source_property_keys - mapped_properties)

		notes = list(selected_rule.notes)
		if vector_match is not None:
			notes.append(
				"Hybrid retrieval used pgvector cosine similarity with exact type filter."
			)
		if property_rules:
			notes.append(
				f"Applied {len(property_rules)} property mapping rules for {resource.resource_type.value}."
			)
		if unmapped_properties:
			notes.append(
				f"Detected {len(unmapped_properties)} unmapped properties requiring review."
			)

		return MappingRecord(
			source_resource_id=resource.resource_id,
			target_logical_id=logical_id,
			mapping_rule_id=selected_rule.rule_id,
			confidence=selected_rule.confidence,
			notes=notes,
			unmapped_properties=unmapped_properties,
		)

	def _hybrid_vector_lookup(self, resource: SourceResource) -> VectorMatch | None:
		if not self._database_url:
			return None

		query_text = _build_retrieval_query_text(resource)
		embedding = self._embed_text(query_text)
		if not embedding:
			return None

		# First pass: exact Azure type filter with vector ordering.
		matches = self._query_vector_matches(
			embedding=embedding,
			azure_resource_type=resource.resource_type.value,
			top_k=self._top_k,
		)
		if not matches:
			# Second pass: semantic-only if typed subset is empty.
			matches = self._query_vector_matches(
				embedding=embedding,
				azure_resource_type=None,
				top_k=self._top_k,
			)

		if not matches:
			return None

		best = matches[0]
		if best.distance > self._max_vector_distance:
			return None
		return best

	def _embed_text(self, text: str) -> list[float] | None:
		if not text.strip():
			return None
		if not self._embedding_model_id:
			return None
		if boto3 is None:
			return None

		try:
			client = self._bedrock_runtime_client
			if client is None:
				client = boto3.client(
					"bedrock-runtime",
					region_name=self._embedding_region_name,
				)
				self._bedrock_runtime_client = client

			payload = json.dumps({"inputText": text})
			response = client.invoke_model(
				modelId=self._embedding_model_id,
				contentType="application/json",
				accept="application/json",
				body=payload,
			)
			body = response.get("body")
			data = json.loads(body.read().decode("utf-8") if body else "{}")
			embedding = data.get("embedding")
			if isinstance(embedding, list) and embedding:
				return [float(v) for v in embedding]
		except Exception as exc:  # pragma: no cover - provider/runtime failures
			logger.warning("rag_retriever: embedding generation failed: %s", exc)

		return None

	def _query_vector_matches(
		self,
		*,
		embedding: list[float],
		azure_resource_type: str | None,
		top_k: int,
	) -> list[VectorMatch]:
		vector_literal = _to_pgvector_literal(embedding)
		if psycopg is None:
			return []
		params: list[Any] = [vector_literal]

		if azure_resource_type:
			sql = """
				SELECT
					id::text,
					aws_resource_type,
					description,
					1 - (embedding <=> %s::vector) AS similarity,
					embedding <=> %s::vector AS distance
				FROM mapping_rules
				WHERE azure_resource_type = %s
				  AND embedding IS NOT NULL
				ORDER BY embedding <=> %s::vector
				LIMIT %s
			"""
			params.extend([vector_literal, azure_resource_type, vector_literal, top_k])
		else:
			sql = """
				SELECT
					id::text,
					aws_resource_type,
					description,
					1 - (embedding <=> %s::vector) AS similarity,
					embedding <=> %s::vector AS distance
				FROM mapping_rules
				WHERE embedding IS NOT NULL
				ORDER BY embedding <=> %s::vector
				LIMIT %s
			"""
			params.extend([vector_literal, vector_literal, top_k])

		try:
			with psycopg.connect(self._database_url) as conn:
				with conn.cursor() as cur:
					cur.execute(sql, tuple(params))
					rows = cur.fetchall()
		except Exception as exc:  # pragma: no cover - infra/runtime failures
			logger.warning("rag_retriever: pgvector lookup failed: %s", exc)
			return []

		result: list[VectorMatch] = []
		for row in rows:
			rule_id = f"kb-{row[0]}"
			aws_resource_type = str(row[1])
			description = str(row[2]) if row[2] else ""
			similarity = float(row[3]) if row[3] is not None else 0.0
			distance = float(row[4]) if row[4] is not None else 1.0
			confidence = max(0.0, min(1.0, similarity))
			notes = (description,) if description else ()
			result.append(
				VectorMatch(
					rule_id=rule_id,
					aws_resource_type=aws_resource_type,
					confidence=confidence,
					distance=distance,
					notes=notes,
				)
			)
		return result


def _build_logical_id(resource_name: str, aws_resource_type: str) -> str:
	normalized = "".join(ch if ch.isalnum() else " " for ch in resource_name)
	title = "".join(part.capitalize() for part in normalized.split()) or "Resource"
	suffix = aws_resource_type.split("::")[-1]
	return f"{title}{suffix}"


def _build_retrieval_query_text(resource: SourceResource) -> str:
	property_names = sorted(resource.properties.keys())
	property_text = ", ".join(property_names) if property_names else "<none>"
	return (
		f"Azure resource type: {resource.resource_type.value}\n"
		f"Resource name: {resource.name}\n"
		f"Location: {resource.location}\n"
		f"Property keys: {property_text}"
	)


def _to_pgvector_literal(values: list[float]) -> str:
	joined = ",".join(f"{value:.8f}" for value in values)
	return f"[{joined}]"


def _default_mapping_file_path() -> Path:
	repo_root = Path(__file__).resolve().parents[3]
	return repo_root / "knowledge_base" / "data" / "resource_type_mappings.json"


def _load_rules_from_json(
	mapping_file_path: str | None,
) -> dict[ResourceType, MappingRule]:
	path = Path(mapping_file_path) if mapping_file_path else _default_mapping_file_path()
	if not path.is_file():
		return {}

	data = json.loads(path.read_text(encoding="utf-8"))
	items = data.get("mappings", [])
	rules: dict[ResourceType, MappingRule] = {}

	for item in items:
		resource_type_value = item.get("azure_resource_type")
		if resource_type_value not in {member.value for member in ResourceType}:
			continue

		resource_type = ResourceType(resource_type_value)
		rule = MappingRule(
			rule_id=item.get("mapping_rule_id", f"rule-{resource_type.name.lower()}"),
			aws_resource_type=item.get("aws_resource_type", ""),
			confidence=float(item.get("confidence", 0.0)),
			notes=tuple(item.get("notes", [])),
		)
		if not rule.aws_resource_type:
			continue
		rules[resource_type] = rule

	return rules
