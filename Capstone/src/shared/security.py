from __future__ import annotations

from typing import Any

SECRET_KEYS = {
    "password",
    "passwd",
    "token",
    "secret",
    "secretvalue",
    "clientsecret",
    "apikey",
    "accesskey",
}


def redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, child in value.items():
            normalized = key.replace("_", "").replace("-", "").lower()
            if normalized in SECRET_KEYS:
                redacted[key] = "***REDACTED***"
            else:
                redacted[key] = redact_sensitive(child)
        return redacted
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    return value
