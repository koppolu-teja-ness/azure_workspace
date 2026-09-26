from observability.langsmith_config import build_tracing_config


def test_build_tracing_config_defaults() -> None:
    config = build_tracing_config({})

    assert config.enabled is False
    assert config.provider == "langsmith"
    assert config.project == "azure-aws-migration-assistant"
    assert config.to_env()["LANGCHAIN_TRACING_V2"] == "false"


def test_build_tracing_config_custom_values() -> None:
    config = build_tracing_config(
        {
            "observability": {
                "tracing": {
                    "enabled": True,
                    "provider": "langfuse",
                    "project": "capstone-pipeline",
                    "endpoint": "https://api.smith.langchain.com",
                }
            }
        }
    )

    env = config.to_env()
    assert config.enabled is True
    assert config.provider == "langfuse"
    assert env["LANGCHAIN_TRACING_V2"] == "true"
    assert env["LANGCHAIN_PROJECT"] == "capstone-pipeline"
    assert env["LANGCHAIN_ENDPOINT"] == "https://api.smith.langchain.com"