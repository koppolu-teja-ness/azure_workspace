"""End-to-end pipeline: Bicep file -> CloudFormation YAML, with static validation
and a self-correction loop that feeds cfn-lint errors back to the generator.
"""
from __future__ import annotations

import json
from pathlib import Path

from .bicep_compiler import BicepCompilerError, compile_bicep_to_arm
from .config import Config
from .generator import Generator, GeneratorNotConfiguredError, build_prompt
from .knowledge_base import KnowledgeBase
from .resource_extractor import extract_resource_types
from .validator import run_cfn_lint


class UnmappedResourceError(RuntimeError):
    """Raised when the Bicep template uses a resource type with no knowledge-base doc."""


class PipelineResult:
    def __init__(self, resource_types: list[str], output_path: Path | None,
                 lint_passed: bool | None, lint_output: str | None):
        self.resource_types = resource_types
        self.output_path = output_path
        self.lint_passed = lint_passed
        self.lint_output = lint_output


def run_pipeline(
    bicep_path: Path,
    output_dir: Path,
    knowledge_base: KnowledgeBase,
    generator: Generator | None,
    config: Config,
    dry_run: bool = False,
) -> PipelineResult:
    # 1. Compile Bicep -> ARM JSON (stable structure to parse resource types from)
    arm_template = compile_bicep_to_arm(bicep_path)

    # 2. Identify resource types in use
    resource_types = extract_resource_types(arm_template)

    # 3. Knowledge lookup: stop and flag anything with no mapping doc yet
    missing = knowledge_base.missing_types(resource_types)
    if missing:
        raise UnmappedResourceError(
            "The following resource types have no mapping doc in the knowledge "
            f"base yet, add one before continuing: {', '.join(missing)}"
        )

    if dry_run:
        return PipelineResult(resource_types, None, None, None)

    if generator is None:
        raise GeneratorNotConfiguredError(
            "No generator configured. Set up Bedrock credentials or pass --dry-run."
        )

    mapping_docs = knowledge_base.load_docs(resource_types)
    bicep_source = bicep_path.read_text(encoding="utf-8")
    arm_json_text = json.dumps(arm_template, indent=2)

    prompt = build_prompt(bicep_source, arm_json_text, mapping_docs, resource_types)
    yaml_text = generator.generate(prompt)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{bicep_path.stem}.generated.yaml"
    output_path.write_text(yaml_text, encoding="utf-8")

    lint_passed, lint_output = run_cfn_lint(output_path)

    attempts = 0
    while not lint_passed and attempts < config.max_fix_attempts:
        attempts += 1
        fix_prompt = (
            f"The CloudFormation template you generated failed cfn-lint with the "
            f"following output:\n\n{lint_output}\n\nHere is the template:\n\n"
            f"```yaml\n{yaml_text}\n```\n\nFix the issues and return the complete "
            f"corrected YAML template only."
        )
        yaml_text = generator.generate(fix_prompt)
        output_path.write_text(yaml_text, encoding="utf-8")
        lint_passed, lint_output = run_cfn_lint(output_path)

    return PipelineResult(resource_types, output_path, lint_passed, lint_output)
