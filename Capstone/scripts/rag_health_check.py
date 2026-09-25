"""RAG readiness health-check for local/dev pipeline runs.

Checks:
1) dependency availability (boto3, psycopg),
2) Postgres connectivity,
3) pgvector extension + KB schema table availability,
4) optional Bedrock embedding model invocation.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    status: str
    detail: str


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG readiness health-check")
    parser.add_argument(
        "--database-url",
        default=os.getenv("RAG_DATABASE_URL") or os.getenv("DATABASE_URL"),
        help="Postgres URL for pgvector KB (default: RAG_DATABASE_URL or DATABASE_URL)",
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
    parser.add_argument(
        "--skip-bedrock",
        action="store_true",
        help="Skip active Bedrock invoke_model check",
    )
    args = parser.parse_args()

    results: list[CheckResult] = []

    boto3 = _try_import("boto3", results)
    psycopg = _try_import("psycopg", results)

    if not args.database_url:
        results.append(
            CheckResult(
                name="database_url",
                status="fail",
                detail="DATABASE_URL/RAG_DATABASE_URL is not set.",
            )
        )
    elif psycopg is None:
        results.append(
            CheckResult(
                name="postgres_connectivity",
                status="fail",
                detail="psycopg is unavailable.",
            )
        )
    else:
        results.extend(_check_postgres(psycopg, args.database_url))

    if args.skip_bedrock:
        results.append(
            CheckResult(
                name="bedrock_embedding_invoke",
                status="skip",
                detail="Skipped by --skip-bedrock.",
            )
        )
    else:
        results.extend(
            _check_bedrock(
                boto3=boto3,
                model_id=args.embedding_model_id,
                region=args.region,
            )
        )

    _print_summary(results)
    failed = [result for result in results if result.status == "fail"]
    if failed:
        raise SystemExit(1)


def _try_import(module_name: str, results: list[CheckResult]) -> Any | None:
    try:
        module = __import__(module_name)
    except Exception as exc:
        results.append(
            CheckResult(
                name=f"dependency:{module_name}",
                status="fail",
                detail=f"Import failed: {exc}",
            )
        )
        return None

    results.append(
        CheckResult(
            name=f"dependency:{module_name}",
            status="ok",
            detail="Import succeeded.",
        )
    )
    return module


def _check_postgres(psycopg: Any, database_url: str) -> list[CheckResult]:
    results: list[CheckResult] = []
    try:
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
                results.append(
                    CheckResult(
                        name="postgres_connectivity",
                        status="ok",
                        detail="Connected successfully.",
                    )
                )

                cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                extension = cur.fetchone()
                if extension:
                    results.append(
                        CheckResult(
                            name="pgvector_extension",
                            status="ok",
                            detail="vector extension is installed.",
                        )
                    )
                else:
                    results.append(
                        CheckResult(
                            name="pgvector_extension",
                            status="fail",
                            detail="vector extension is missing.",
                        )
                    )

                for table in (
                    "mapping_rules",
                    "rbac_iam_mappings",
                    "trigger_mappings",
                    "incompatibilities",
                ):
                    cur.execute(
                        """
                        SELECT EXISTS (
                            SELECT 1
                            FROM information_schema.tables
                            WHERE table_schema = 'public'
                              AND table_name = %s
                        )
                        """,
                        (table,),
                    )
                    exists = bool(cur.fetchone()[0])
                    status = "ok" if exists else "fail"
                    detail = "Table exists." if exists else "Table missing."
                    results.append(CheckResult(name=f"table:{table}", status=status, detail=detail))

                cur.execute("SELECT COUNT(*) FROM mapping_rules WHERE embedding IS NOT NULL")
                populated = int(cur.fetchone()[0])
                if populated > 0:
                    results.append(
                        CheckResult(
                            name="mapping_rules_embeddings",
                            status="ok",
                            detail=f"{populated} row(s) have embeddings.",
                        )
                    )
                else:
                    results.append(
                        CheckResult(
                            name="mapping_rules_embeddings",
                            status="warn",
                            detail="No embedded mapping rows found. Run seed ingestion.",
                        )
                    )
    except Exception as exc:
        results.append(
            CheckResult(
                name="postgres_connectivity",
                status="fail",
                detail=f"Connection/query failed: {exc}",
            )
        )

    return results


def _check_bedrock(*, boto3: Any | None, model_id: str, region: str | None) -> list[CheckResult]:
    results: list[CheckResult] = []
    if boto3 is None:
        results.append(
            CheckResult(
                name="bedrock_embedding_invoke",
                status="fail",
                detail="boto3 is unavailable.",
            )
        )
        return results

    if not model_id:
        results.append(
            CheckResult(
                name="bedrock_embedding_model",
                status="fail",
                detail="Embedding model id is missing.",
            )
        )
        return results

    try:
        runtime = boto3.client("bedrock-runtime", region_name=region)
        payload = json.dumps({"inputText": "RAG health check"})
        response = runtime.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=payload,
        )
        body = response.get("body")
        data = json.loads(body.read().decode("utf-8") if body else "{}")
        embedding = data.get("embedding", [])
        if isinstance(embedding, list) and embedding:
            results.append(
                CheckResult(
                    name="bedrock_embedding_invoke",
                    status="ok",
                    detail=f"Model reachable; embedding length={len(embedding)}.",
                )
            )
        else:
            results.append(
                CheckResult(
                    name="bedrock_embedding_invoke",
                    status="fail",
                    detail="Model returned no embedding vector.",
                )
            )
    except Exception as exc:
        results.append(
            CheckResult(
                name="bedrock_embedding_invoke",
                status="fail",
                detail=f"Invoke failed: {exc}",
            )
        )
    return results


def _print_summary(results: list[CheckResult]) -> None:
    payload = {
        "ok": [result.__dict__ for result in results if result.status == "ok"],
        "warn": [result.__dict__ for result in results if result.status == "warn"],
        "fail": [result.__dict__ for result in results if result.status == "fail"],
        "skip": [result.__dict__ for result in results if result.status == "skip"],
    }
    json.dump(payload, fp=sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()