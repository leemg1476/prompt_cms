# DB Detailed Implementation Plan

## Scope
- PostgreSQL schema for prompt versioning and push delivery tracking.
- SQL bootstrap script + dockerized local database.

## Schema
- `prompts`
- `prompt_versions`
- `prompt_active_pointer`
- `agent_registry`
- `prompt_subscriptions`
- `publish_events`
- `push_deliveries`
- `agent_idempotency_keys` (for internal endpoint safety)

## Constraints
- Unique prompt key
- Unique version per prompt
- Unique subscription pair
- Unique delivery pair per publish event
- Status checks for enum-like columns

## Operational Indexes
- prompt/version status lookup
- enabled agents by env
- pending deliveries by retry time
- publish event query by date

## Seed Data
- one local agent in `dev`
- optional sample prompt and subscription

## Local Runtime
- Docker Compose with `postgres:16`
- Persistent volume `pgdata`
- SQL loaded from `db/init.sql`
