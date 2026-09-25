import json
import subprocess
from pathlib import Path

from migration_assistant.graph.state import ValidationStatus
from migration_assistant.validation.static import cfn_lint_runner, checkov_runner


def test_cfn_lint_runner_returns_pass_when_no_findings(monkeypatch) -> None:
    completed = subprocess.CompletedProcess(
        args=["cfn-lint"],
        returncode=0,
        stdout="[]",
        stderr="",
    )
    monkeypatch.setattr(
        cfn_lint_runner,
        "_run_command",
        lambda primary_command, fallback_command: completed,
    )

    results = cfn_lint_runner.run_cfn_lint(Path("template.yaml"), run_id="run-1")

    assert len(results) == 1
    assert results[0].status == ValidationStatus.PASS
    assert results[0].check_name == "cfn-lint"


def test_cfn_lint_runner_maps_error_to_resource_id(monkeypatch) -> None:
    payload = [
        {
            "Rule": {"Id": "E3001"},
            "Level": "Error",
            "Message": "Invalid property",
            "Location": {
                "Path": ["Resources", "CoreVpc", "Properties", "BadField"],
                "Start": {"LineNumber": 14},
            },
        }
    ]
    completed = subprocess.CompletedProcess(
        args=["cfn-lint"],
        returncode=2,
        stdout=json.dumps(payload),
        stderr="",
    )
    monkeypatch.setattr(
        cfn_lint_runner,
        "_run_command",
        lambda primary_command, fallback_command: completed,
    )

    results = cfn_lint_runner.run_cfn_lint(Path("template.yaml"), run_id="run-1")

    assert len(results) == 1
    assert results[0].status == ValidationStatus.FAIL
    assert results[0].check_name == "E3001"
    assert results[0].resource_id == "CoreVpc"


def test_checkov_runner_returns_failed_checks(monkeypatch) -> None:
    payload = {
        "results": {
            "failed_checks": [
                {
                    "check_id": "CKV_AWS_20",
                    "check_name": "S3 bucket should have public access blocked",
                    "resource": "Resources.MyBucket",
                    "file_line_range": [10, 20],
                    "guideline": "https://docs.bridgecrew.io/docs/s3_1-s3-bucket-public-read-prohibited",
                }
            ],
            "passed_checks": [],
            "skipped_checks": [],
        },
        "summary": {"passed": 0, "failed": 1, "skipped": 0},
    }
    completed = subprocess.CompletedProcess(
        args=["checkov"],
        returncode=1,
        stdout=json.dumps(payload),
        stderr="",
    )
    monkeypatch.setattr(
        checkov_runner,
        "_run_command",
        lambda primary_command, fallback_command: completed,
    )

    results = checkov_runner.run_checkov(Path("template.yaml"), run_id="run-1")

    assert len(results) == 1
    assert results[0].status == ValidationStatus.FAIL
    assert results[0].check_name == "CKV_AWS_20"
    assert results[0].resource_id == "MyBucket"


def test_checkov_runner_warns_when_tool_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        checkov_runner,
        "_run_command",
        lambda primary_command, fallback_command: None,
    )

    results = checkov_runner.run_checkov(Path("template.yaml"), run_id="run-1")

    assert len(results) == 1
    assert results[0].status == ValidationStatus.WARNING
    assert results[0].check_name == "checkov"
