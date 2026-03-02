# Backend Detailed Implementation Plan

## Scope
- Build a single FastAPI service with:
- CMS prompt APIs
- publish/rollback flow
- push delivery worker endpoint
- internal agent push endpoint

## Modules
- `core/config.py`: environment config
- `core/db.py`: SQLAlchemy engine/session
- `models/entities.py`: ORM models
- `schemas/*.py`: request/response schemas
- `services/publish_service.py`: transaction and outbox creation
- `services/worker_service.py`: delivery execution/retry
- `routers/prompts.py`: prompt APIs
- `routers/worker.py`: manual worker trigger APIs
- `routers/internal_push.py`: agent internal endpoint

## Data Flow
1. Draft save
- upsert prompt key
- create `prompt_versions` row with status=`draft`

2. Publish
- create active version from latest draft
- update active pointer
- create publish event
- create one delivery per subscribed agent
- trigger worker once immediately (best effort)

3. Worker run
- pull pending deliveries due for retry
- send HTTP POST to agent endpoint
- payload includes `deployment_mode=yaml_file_sync`
- mark success or schedule retry

## Retry Policy
- Backoff sequence (minutes): 1, 2, 5, 10, 30, 60
- Max attempts: 10
- 4xx: fail immediately
- network/5xx: retry

## Internal Push Endpoint
- Path: `POST /internal/prompts/push`
- Header: `Idempotency-Key` required
- Logic:
- reject missing key
- if key already seen, return `applied=false`
- compare checksum to current cache
- update in-memory cache on change

## API Surface (initial)
- `GET /api/prompts`
- `GET /api/prompts/{prompt_key}`
- `POST /api/prompts/{prompt_key}/draft`
- `POST /api/prompts/{prompt_key}/publish`
- `POST /api/prompts/{prompt_key}/rollback`
- `GET /api/publish-events`
- `POST /api/worker/run-once`

## Run/Env
- `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/prompt_cms`
- `PUSH_AUTH_TOKEN=local-dev-token`
