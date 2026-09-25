-- RAG knowledge base schema (Phase 0 — agree this shape jointly; charan
-- owns populating content in Phase 1, per team-work-split-plan.md).
--
-- Run against a Postgres instance with the pgvector extension available.
-- Loaded automatically by docker-compose.yml for local dev.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- for gen_random_uuid()

-- Bicep resource type -> CloudFormation resource type + property-level
-- mapping rules. This is the core table the Mapping Agent retrieves against.
CREATE TABLE IF NOT EXISTS mapping_rules (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    azure_resource_type TEXT NOT NULL,           -- e.g. 'Microsoft.KeyVault/vaults'
    aws_resource_type   TEXT NOT NULL,           -- e.g. 'AWS::SecretsManager::Secret'
    property_mapping    JSONB NOT NULL DEFAULT '{}',
    description         TEXT,
    source              TEXT,                    -- doc link / internal note
    embedding           VECTOR(1536),             -- match your embedding model's dim
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Azure RBAC role -> IAM policy statement patterns.
CREATE TABLE IF NOT EXISTS rbac_iam_mappings (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    azure_rbac_role   TEXT NOT NULL,
    iam_policy_json   JSONB NOT NULL,
    notes             TEXT,
    embedding         VECTOR(1536),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Trigger mapping rules: HTTP/Timer/Blob/Queue -> API Gateway/EventBridge/S3/SQS.
CREATE TABLE IF NOT EXISTS trigger_mappings (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    azure_trigger_type TEXT NOT NULL,
    aws_equivalent     TEXT NOT NULL,
    config_template    JSONB NOT NULL DEFAULT '{}',
    embedding          VECTOR(1536),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Known incompatibilities and documented workarounds.
CREATE TABLE IF NOT EXISTS incompatibilities (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    azure_concept TEXT NOT NULL,      -- e.g. 'Key Vault soft-delete'
    aws_concept   TEXT NOT NULL,      -- e.g. 'Secrets Manager recovery window'
    description   TEXT NOT NULL,
    workaround    TEXT,
    embedding     VECTOR(1536),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Azure region <-> AWS region mapping, kept in the KB so the Mapping Agent
-- can retrieve it the same way as everything else (mirrors
-- config/region_mapping.yaml, which is the source of truth for local runs).
CREATE TABLE IF NOT EXISTS region_mappings (
    azure_region TEXT PRIMARY KEY,
    aws_region   TEXT NOT NULL
);

-- Historical migration issue log — grows as the agent encounters new edge
-- cases across runs; feeds the "self-improving knowledge base" future work.
CREATE TABLE IF NOT EXISTS migration_issue_log (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id       TEXT NOT NULL,
    resource_id  TEXT,
    issue        TEXT NOT NULL,
    resolution   TEXT,
    embedding    VECTOR(1536),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS mapping_rules_embedding_idx
    ON mapping_rules USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS incompatibilities_embedding_idx
    ON incompatibilities USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
