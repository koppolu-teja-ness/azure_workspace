# High-Level Architecture — Agentic Azure→AWS Migration Assistant

This diagram shows the end-to-end flow: Azure source discovery, the LangGraph multi-agent pipeline, the RAG knowledge base, the human approval gate, AWS deployment, and the supporting application/observability layer.

```mermaid
flowchart TB

    subgraph AZURE["Azure Source Environment"]
        A1["Key Vault"]
        A2["Function Apps"]
        A3["Virtual Network"]
        BICEP["Bicep Templates"]
    end

    subgraph AGENTS["Agentic Migration Pipeline (LangGraph)"]
        D["Discovery Agent"]
        P["Parser / Analyzer Agent"]
        M["Mapping Agent (RAG)"]
        G["CFN Generator Agent"]
        V["Static Validation Agent<br/>cfn-lint, checkov/cfn_nag"]
        R["Planning & Risk-Scoring Agent"]
        DEP["Deployment Agent<br/>boto3 / CloudFormation"]
        PV["Post-Deployment Validation Agent"]
        RPT["Reporting Agent"]
    end

    subgraph KB["Knowledge Base"]
        PG[("PostgreSQL + PGVector<br/>Mapping rules, RBAC/IAM rules,<br/>trigger & region mappings")]
    end

    subgraph GATE["Human-in-the-Loop"]
        H{"Human Approval Gate<br/>Approve / Reject / Modify"}
    end

    subgraph AWSENV["AWS Target Environment"]
        W1["Secrets Manager / KMS / ACM"]
        W2["Lambda + API Gateway /<br/>EventBridge / SQS"]
        W3["VPC, Subnets,<br/>Security Groups, NACLs"]
    end

    subgraph APP["Application Layer"]
        API["FastAPI Backend"]
        UI["Streamlit / React Dashboard"]
    end

    subgraph OBS["Observability"]
        LS["LangSmith / LangFuse<br/>(agent tracing)"]
        CW["CloudWatch /<br/>Prometheus / Grafana"]
    end

    A1 & A2 & A3 --> D
    BICEP --> D
    D --> P --> M
    M <--> PG
    M --> G --> V --> R --> H

    H -- "Approve" --> DEP
    H -- "Reject / Modify" --> M

    DEP --> W1 & W2 & W3
    W1 & W2 & W3 --> PV
    PV --> RPT
    RPT --> UI

    API --> AGENTS
    UI --> API

    AGENTS -. traces .-> LS
    AWSENV -. metrics .-> CW
```

## Component Summary

| Layer | Components | Role |
|---|---|---|
| **Azure Source** | Key Vault, Function Apps, VNet, Bicep templates | The environment being migrated |
| **Agent Pipeline** | Discovery → Parser/Analyzer → Mapping → CFN Generator → Static Validation → Planning/Risk-Scoring → Deployment → Post-Deploy Validation → Reporting | LangGraph-orchestrated agents that carry out discovery, translation, validation, and verification |
| **Knowledge Base** | PostgreSQL + PGVector (RAG store) | Grounds the Mapping Agent in real Bicep→CFN, RBAC→IAM, and trigger-mapping rules instead of free-form LLM guessing |
| **Human-in-the-Loop** | Approval Gate | Mandatory checkpoint before any AWS deployment — Approve / Reject / Modify |
| **AWS Target** | Secrets Manager/KMS/ACM, Lambda+API Gateway/EventBridge/SQS, VPC/Subnets/SGs/NACLs | The deployed, functionally-equivalent AWS environment |
| **Application Layer** | FastAPI backend, Streamlit/React dashboard | Exposes pipeline status, migration plans, and reports to users |
| **Observability** | LangSmith/LangFuse, CloudWatch/Prometheus/Grafana | Agent tracing and infrastructure/runtime monitoring |
