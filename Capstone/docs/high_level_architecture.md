# High-Level Architecture

This document complements [ARCHITECTURE.md](../ARCHITECTURE.md) with a
visual reference and implementation-oriented notes.

## Diagram

Static diagram asset:
- [architecture_diagram.png](architecture_diagram.png)

## System Context

Core parts of the solution:

- Source ingestion: Azure IaC/discovery inputs are normalized into
  `SourceResource` records.
- Workflow engine: LangGraph drives node execution and routing.
- Knowledge and mapping: Deterministic mapping rules and optional semantic
  retrieval support translation.
- Generation and validation: CloudFormation output is produced and checked
  before deployment.
- Approval and deployment: Human approval controls promotion to deployment.
- Reporting and observability: Run artifacts and traces are captured for audit.

## End-to-End Flow

```text
Discovery -> Parse/Analyze -> Map -> Generate CFN -> Static Validate
         -> Plan/Risk -> Human Approval -> Deploy -> Post-Deploy Validate -> Report
```

## Current Implementation Notes

- Graph wiring is implemented in `src/migration_assistant/graph/workflow.py`.
- Shared data contract is implemented in `src/migration_assistant/graph/state.py`.
- Some agents are fully deterministic today, while some LLM-enabled paths are
  partially implemented and still being refined.
- LLM usage relies on AWS Bedrock configuration in runtime state (`config.llm`).

## Related Docs

- [agent_responsibilities.md](agent_responsibilities.md)
- [migration_spec_schema.md](migration_spec_schema.md)
- [mapping_rules_reference.md](mapping_rules_reference.md)
