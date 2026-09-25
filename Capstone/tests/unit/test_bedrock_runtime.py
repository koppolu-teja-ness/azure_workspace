from migration_assistant.config.app_config import parse_app_config
from migration_assistant.llm.bedrock_runtime import (
    extract_text_from_bedrock_response,
    parse_json_object,
    parse_llm_provider_config,
)


def test_parse_llm_provider_config_for_valid_bedrock() -> None:
    raw_config = {
        "llm": {
            "enabled": True,
            "provider": "aws_bedrock",
            "bedrock": {
                "model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
                "region_name": "us-east-1",
                "temperature": 0.1,
                "max_tokens": 512,
            },
        }
    }
    config = parse_app_config(raw_config)

    provider = parse_llm_provider_config(config)

    assert provider.enabled is True
    assert provider.provider == "aws_bedrock"
    assert provider.settings is not None
    assert provider.settings.model_id.startswith("anthropic.claude")
    assert provider.settings.region_name == "us-east-1"


def test_parse_llm_provider_config_without_model_id_disables_settings() -> None:
    raw_config = {
        "llm": {
            "enabled": True,
            "provider": "aws_bedrock",
            "bedrock": {
                "model_id": "",
            },
        }
    }
    config = parse_app_config(raw_config)

    provider = parse_llm_provider_config(config)

    assert provider.enabled is True
    assert provider.provider == "aws_bedrock"
    assert provider.settings is None


def test_parse_llm_provider_config_normalizes_zero_temperature() -> None:
    raw_config = {
        "llm": {
            "enabled": True,
            "provider": "aws_bedrock",
            "bedrock": {
                "model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
                "temperature": 0.0,
            },
        }
    }
    config = parse_app_config(raw_config)

    provider = parse_llm_provider_config(config)

    assert provider.settings is not None
    assert provider.settings.temperature == 0.7


def test_parse_json_object_accepts_wrapped_json() -> None:
    text = "Here is output:\n```json\n{\"a\": 1, \"b\": [2]}\n```"

    parsed = parse_json_object(text)

    assert parsed == {"a": 1, "b": [2]}


def test_extract_text_from_bedrock_response_concatenates_text_items() -> None:
    payload = {
        "content": [
            {"type": "text", "text": "line one"},
            {"type": "tool_use", "name": "ignored"},
            {"type": "text", "text": "line two"},
        ]
    }

    result = extract_text_from_bedrock_response(payload)

    assert result == "line one\nline two"
