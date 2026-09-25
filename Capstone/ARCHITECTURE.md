# Architecture Overview

This project is a LangGraph-based, agentic workflow for Azure-to-AWS
infrastructure migration.

## Architecture diagram

- High-level architecture notes: [docs/high_level_architecture.md](docs/high_level_architecture.md)
- Diagram asset: [docs/architecture_diagram.png](docs/architecture_diagram.png)

## High-level flow

```text
Discovery -> Parse/Analyze -> Map -> Generate CFN -> Static Validate
				 -> Plan/Risk -> Human Approval -> Deploy -> Post-Deploy Validate -> Report
```

The graph wiring is defined in `src/migration_assistant/graph/workflow.py`.

## Implementation status

- Core graph structure and state contract are implemented.
- Multiple agent paths are still in scaffold/partial mode while the capstone
	implementation is being completed.

## Core architecture components

| Layer | Purpose | Key locations |
|---|---|---|
| Workflow orchestration | Defines node order, conditional routing, and end states | `src/migration_assistant/graph/workflow.py` |
| Agent implementations | Node logic per migration stage | `src/migration_assistant/agents/` |
| Shared state contract | Typed state and migration schema | `src/migration_assistant/graph/state.py` |
| Mapping knowledge base | Rule tables, incompatibilities, pgvector schema | `knowledge_base/` |
| API/UI surfaces | FastAPI endpoints and dashboard/frontends | `api/`, `streamlit_app/`, `dashboard/` |
| Observability | LLM/runtime trace and metrics integrations | `observability/` |

## LLM and RAG placement

### Agents using LLM

- Mapping Agent (`mapping_agent.py`): optional Bedrock mapping enrichment.
- Planning & Risk Agent (`planning_risk_agent.py`): optional Bedrock risk
	reason enrichment.
- Reporting Agent (`reporting_agent.py`): optional Bedrock summary generation.

### Agents using RAG

- Mapping Agent (`mapping_agent.py`) uses `RuleBasedMappingRetriever`.
- Retriever behavior is hybrid:
	- deterministic JSON/rule-table fallback always available,
	- optional pgvector similarity retrieval when DB/embeddings are configured.

## Runtime behavior

- LLM-capable modules use a shared Bedrock runtime helper contract.
- Required Bedrock settings are validated by `require_bedrock_settings(...)`
	where used.
- LLM-capable agent implementations append `llm_traces` into graph state when
	their LLM path executes.

## Configuration contract for LLM execution

LLM calls are enabled only when state config contains:

```yaml
llm:
	enabled: true
	provider: aws_bedrock
	bedrock:
		model_id: <non-empty>
		region_name: us-east-1
		temperature: 0.7
		max_tokens: 800
```

If a node calls `require_bedrock_settings(...)` and config is incomplete, that
node raises a configuration error in the current implementation.
