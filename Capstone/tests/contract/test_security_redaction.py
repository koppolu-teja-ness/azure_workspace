from __future__ import annotations

from shared.security import redact_sensitive


def test_redacts_secret_like_fields() -> None:
    payload = {
        "clientSecret": "super-secret",
        "nested": {
            "token": "abcd",
            "safe": "value",
        },
        "list": [{"apiKey": "123"}],
    }

    redacted = redact_sensitive(payload)
    assert redacted["clientSecret"] == "***REDACTED***"
    assert redacted["nested"]["token"] == "***REDACTED***"
    assert redacted["nested"]["safe"] == "value"
    assert redacted["list"][0]["apiKey"] == "***REDACTED***"
