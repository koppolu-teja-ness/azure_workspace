from __future__ import annotations

import json
from pathlib import Path

from pydantic import TypeAdapter

from shared.contracts.models import DiscoveryOutput


def test_discovery_output_round_trip() -> None:
    payload = json.loads(Path("fixtures/specs/happy-path.json").read_text(encoding="utf-8"))

    discovery_payload = {
        "specVersion": payload["specVersion"],
        "source": payload["source"],
        "target": payload["target"],
        "resources": [
            {
                "id": resource["id"],
                "service_area": resource["serviceArea"],
                "source_type": resource["sourceType"],
                "target_type": resource["targetType"],
                "name": resource["name"],
                "decision": resource["decision"],
                "properties": resource["properties"],
                "notes": resource.get("notes"),
            }
            for resource in payload["resources"]
        ],
        "dependencies": [
            {
                "from": dep["from"],
                "to": dep["to"],
                "kind": dep["kind"],
            }
            for dep in payload["dependencies"]
        ],
        "traceability": payload["traceability"],
    }

    obj = DiscoveryOutput.model_validate(discovery_payload)
    serialized = obj.model_dump(by_alias=True)
    adapter = TypeAdapter(DiscoveryOutput)
    round_trip = adapter.validate_python(serialized)

    assert round_trip == obj
