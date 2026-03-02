CREATE TABLE IF NOT EXISTS prompts (
  id BIGSERIAL PRIMARY KEY,
  prompt_key VARCHAR(200) NOT NULL UNIQUE,
  description TEXT,
  owner_team VARCHAR(100),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS prompt_versions (
  id BIGSERIAL PRIMARY KEY,
  prompt_id BIGINT NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
  version INTEGER NOT NULL,
  status VARCHAR(20) NOT NULL CHECK (status IN ('draft', 'active', 'archived')),
  content TEXT NOT NULL,
  variables_schema JSONB,
  checksum VARCHAR(64) NOT NULL,
  created_by VARCHAR(100),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (prompt_id, version)
);

CREATE INDEX IF NOT EXISTS idx_prompt_versions_prompt_status
  ON prompt_versions(prompt_id, status);

CREATE TABLE IF NOT EXISTS prompt_active_pointer (
  prompt_id BIGINT PRIMARY KEY REFERENCES prompts(id) ON DELETE CASCADE,
  active_version_id BIGINT NOT NULL REFERENCES prompt_versions(id),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_registry (
  id BIGSERIAL PRIMARY KEY,
  agent_name VARCHAR(100) NOT NULL,
  environment VARCHAR(20) NOT NULL,
  base_url TEXT NOT NULL,
  push_endpoint TEXT NOT NULL DEFAULT '/internal/prompts/push',
  auth_type VARCHAR(20) NOT NULL DEFAULT 'bearer',
  auth_secret_ref TEXT,
  is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_registry_env_enabled
  ON agent_registry(environment, is_enabled);

CREATE TABLE IF NOT EXISTS prompt_subscriptions (
  id BIGSERIAL PRIMARY KEY,
  prompt_id BIGINT NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
  agent_id BIGINT NOT NULL REFERENCES agent_registry(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (prompt_id, agent_id)
);

CREATE TABLE IF NOT EXISTS publish_events (
  id BIGSERIAL PRIMARY KEY,
  prompt_id BIGINT NOT NULL REFERENCES prompts(id),
  version_id BIGINT NOT NULL REFERENCES prompt_versions(id),
  environment VARCHAR(20) NOT NULL,
  published_by VARCHAR(100),
  published_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS push_deliveries (
  id BIGSERIAL PRIMARY KEY,
  publish_event_id BIGINT NOT NULL REFERENCES publish_events(id) ON DELETE CASCADE,
  agent_id BIGINT NOT NULL REFERENCES agent_registry(id),
  idempotency_key VARCHAR(80) NOT NULL,
  attempt INTEGER NOT NULL DEFAULT 0,
  status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'success', 'failed')),
  last_error TEXT,
  last_http_status INTEGER,
  next_retry_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (publish_event_id, agent_id)
);

CREATE INDEX IF NOT EXISTS idx_push_deliveries_pending_retry
  ON push_deliveries(status, next_retry_at);

CREATE TABLE IF NOT EXISTS agent_idempotency_keys (
  id BIGSERIAL PRIMARY KEY,
  idempotency_key VARCHAR(120) NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO agent_registry (agent_name, environment, base_url, push_endpoint, auth_type, auth_secret_ref)
VALUES ('local-agent', 'dev', 'http://agent:8010', '/internal/prompts/push', 'bearer', 'PUSH_AUTH_TOKEN')
ON CONFLICT DO NOTHING;
