"""Generation step: turns a Bicep/ARM source + mapping docs into a CFN YAML draft.

The LLM call is isolated behind the Generator interface so the rest of the
pipeline (parsing, knowledge lookup, validation) works and is testable today,
before AWS Bedrock credentials are configured. Swap in a different backend by
implementing Generator.generate() (e.g. Azure OpenAI, OpenAI) without touching
pipeline.py.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from .config import Config

SYSTEM_PROMPT = """You are an expert cloud migration engineer. You convert Azure \
Bicep/ARM templates into equivalent AWS CloudFormation YAML templates.

Rules:
- Use the provided mapping reference doc(s) as the authoritative source for \
resource/parameter/property mapping decisions; do not invent mappings that \
contradict them.
- Preserve parameter names' intent (e.g. secure params -> NoEcho: true).
- Output ONLY the final CloudFormation YAML, no commentary, no markdown fences.
"""


class GeneratorNotConfiguredError(RuntimeError):
    pass


class Generator(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Return raw CloudFormation YAML text for the given user prompt."""


class BedrockGenerator(Generator):
    """Calls an AWS Bedrock model (e.g. an Anthropic Claude model) to generate YAML.

    Requires: `pip install boto3` and AWS credentials with `bedrock:InvokeModel`
    permission for `config.bedrock_model_id` in `config.aws_region`.
    """

    def __init__(self, config: Config):
        self.config = config
        try:
            import boto3  # noqa: F401
        except ImportError as exc:
            raise GeneratorNotConfiguredError(
                "boto3 is not installed. Run 'pip install boto3' to enable "
                "the Bedrock generator."
            ) from exc
        self._boto3 = boto3

    def _client(self):
        try:
            return self._boto3.client(
                "bedrock-runtime", region_name=self.config.aws_region
            )
        except Exception as exc:  # e.g. NoCredentialsError
            raise GeneratorNotConfiguredError(
                "Could not create a Bedrock client. Configure AWS credentials "
                "(aws configure / env vars) with bedrock:InvokeModel access."
            ) from exc

    def generate(self, prompt: str) -> str:
        import json

        client = self._client()
        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
            }
        )
        response = client.invoke_model(
            modelId=self.config.bedrock_model_id,
            body=body,
        )
        payload = json.loads(response["body"].read())
        return payload["content"][0]["text"]


def build_prompt(
    bicep_source: str,
    arm_json: str,
    mapping_docs: dict[str, str],
    resource_types: list[str],
) -> str:
    docs_section = "\n\n".join(
        f"### Reference doc for {rtype}\n{doc}" for rtype, doc in mapping_docs.items()
    )
    return f"""Convert the following Azure Bicep template (and its compiled ARM JSON) \
into an AWS CloudFormation YAML template.

Resource types present: {", ".join(resource_types)}

## Bicep source
```bicep
{bicep_source}
```

## Compiled ARM JSON
```json
{arm_json}
```

## Mapping reference docs
{docs_section}

Produce the complete CloudFormation YAML template now.
"""
