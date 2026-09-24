from __future__ import annotations

import hashlib
import json
from typing import Any

from .spec import validate_migration_spec_payload


def parse_and_build_intermediate(payload: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic summary consumed by the target pipeline."""
    validate_migration_spec_payload(payload)

    resources = payload["resources"]
    ordered_ids = sorted(str(resource["id"]) for resource in resources)
    digest = hashlib.sha256("|".join(ordered_ids).encode("utf-8")).hexdigest()

    return {
        "specVersion": payload["specVersion"],
        "resourceCount": len(resources),
        "resourceIds": ordered_ids,
        "riskClassification": payload["risk"]["classification"],
        "fingerprint": digest,
    }


def parse_file_and_build_intermediate(file_content: str) -> dict[str, Any]:
    payload = json.loads(file_content)
    return parse_and_build_intermediate(payload)
