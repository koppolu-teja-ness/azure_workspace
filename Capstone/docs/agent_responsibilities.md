# Agent Responsibilities

This document reflects the current Phase 0/1 implementation in
`src/migration_assistant/agents` and the workflow wiring in
`src/migration_assistant/graph/workflow.py`.

## Workflow order

1. `discovery`
2. `parse_analyze`
3. `map`
4. `generate_cfn`
5. `static_validate`
6. `plan_risk`
7. `human_approval`
8. `deploy`
9. `post_deploy_validate`
10. `report`

## Agent matrix

| Agent node | Primary responsibility | Uses RAG? | Uses LLM? | Current implementation notes |
|---|---|---|---|---|
| Discovery Agent | Discover Azure resources and ingest source inputs | No | No | Deterministic/resource ingestion path |
| Parser/Analyzer Agent | Parse Bicep and build source graph context | No | No | Deterministic parsing/normalization |
| Mapping Agent | Map Azure resources/properties to AWS equivalents | Yes | Yes (required in current code path) | Builds deterministic mappings, then attempts Bedrock refinement; current return payload is still stubbed/partial |
| CFN Generator Agent | Generate CloudFormation resources/templates | No | No | Deterministic generation path |
| Static Validation Agent | Lint/security/schema checks on generated templates | No | No | Deterministic validators |
| Planning & Risk Agent | Compute migration risk and reasons | No | Yes (required in current code path) | Deterministic scoring baseline with Bedrock rationale enrichment |
| Human Approval Gate | Approve/reject/modify migration plan | No | No | Control-flow gate node |
| Deployment Agent | Deploy approved templates/resources | No | No | Deterministic deployment orchestration |
| Post-Deploy Validation Agent | Compare deployed AWS state vs source expectations | No | No | Deterministic post-deploy checks |
| Reporting Agent | Produce run summary/report outputs | No | Planned | Current function returns early as a stub before Bedrock summary logic executes |

## Where LLM and RAG are used

- Mapping Agent (`mapping_agent.py`):
	- Uses `RuleBasedMappingRetriever` (hybrid retriever with deterministic and
		optional pgvector retrieval) for mapping rule selection.
	- Uses `BedrockMappingClient` with required Bedrock settings.
- Planning & Risk Agent (`planning_risk_agent.py`):
	- Uses deterministic `assess_risks(...)` first.
	- Uses required `BedrockRiskReasoner` enrichment.
- Reporting Agent (`reporting_agent.py`):
	- Bedrock summary path is drafted (`BedrockReportWriter`) but currently not
		reached because the function returns early in stub mode.

## Configuration behavior summary

- Global LLM provider is read from `GraphState.config.llm`.
- In current LLM-enabled paths, execution requires all of the following:
	- `llm.enabled: true`
	- `llm.provider: "aws_bedrock"`
	- non-empty `llm.bedrock.model_id`
- If those conditions are not met in a required path, the runtime helper raises
  a configuration error.
- Mapping retrieval itself still has deterministic rule-table behavior even
  without vector DB infrastructure.

## Traceability

- LLM-capable agents append trace records to `llm_traces` in state.
- This preserves observability for required LLM calls.

