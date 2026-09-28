from migration_assistant.agents import parser_analyzer_agent
from migration_assistant.bicep_parser.models import ParsedBicepResource
from migration_assistant.graph.state import MigrationStatus


def test_parser_analyzer_uses_cli_compile_when_available(monkeypatch) -> None:
    monkeypatch.setattr(
        parser_analyzer_agent,
        "compile_bicep_file_to_arm_resources",
        lambda path: type(
            "CompileResult",
            (),
            {
                "resources": [
                    {
                        "type": "Microsoft.KeyVault/vaults",
                        "apiVersion": "2023-07-01",
                        "name": "kv-cli",
                        "location": "eastus",
                        "properties": {"tenantId": "x"},
                    }
                ],
                "provenance": "azure_cli_compile",
            },
        )(),
    )
    monkeypatch.setattr(parser_analyzer_agent, "parse_bicep_file", lambda path: [])

    state = {
        "run_id": "parser-cli-1",
        "config": {
            "discovered_bicep_files": ["tests/fixtures/sample_bicep/keyvault.bicep"],
            "parser": {
                "prefer_azure_cli_compile": True,
                "allow_fallback_parser": True,
            },
        },
    }

    update = parser_analyzer_agent.run(state)

    assert update["status"] == MigrationStatus.PARSED
    assert len(update["source_resources"]) == 1
    assert update["source_resources"][0].name == "kv-cli"
    assert update["config"]["parser_provenance"][0]["parser"] == "azure_cli_compile"


def test_parser_analyzer_falls_back_to_ast_parser(monkeypatch) -> None:
    monkeypatch.setattr(
        parser_analyzer_agent,
        "compile_bicep_file_to_arm_resources",
        lambda path: None,
    )
    monkeypatch.setattr(
        parser_analyzer_agent,
        "parse_bicep_file",
        lambda path: [
            ParsedBicepResource(
                symbolic_name="kvFallback",
                resource_type="Microsoft.KeyVault/vaults",
                api_version="2023-07-01",
                name="kv-fallback",
                location="eastus",
                properties={"tenantId": "__present__"},
            )
        ],
    )

    state = {
        "run_id": "parser-fallback-1",
        "config": {
            "discovered_bicep_files": ["tests/fixtures/sample_bicep/keyvault.bicep"],
            "parser": {
                "prefer_azure_cli_compile": True,
                "allow_fallback_parser": True,
            },
        },
    }

    update = parser_analyzer_agent.run(state)

    assert update["status"] == MigrationStatus.PARSED
    assert len(update["source_resources"]) == 1
    assert update["source_resources"][0].name == "kv-fallback"
    assert update["config"]["parser_provenance"][0]["parser"] == "fallback_ast_parser"
