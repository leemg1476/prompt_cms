# Frontend Detailed Implementation Plan

## Scope
- Build a Next.js admin app for prompt operations.
- Pages: prompt list, prompt detail/editor, publish history.
- Integrate directly with FastAPI backend via REST.

## Tech Stack
- Next.js App Router + React + TypeScript
- Native fetch (simple) + server actions optional
- Minimal CSS with global stylesheet

## Route Design
1. `/`
- Redirect to `/prompts`.

2. `/prompts`
- Fetch prompt list: `GET /api/prompts`.
- Show key metadata: `prompt_key`, `description`, `owner_team`, `updated_at`.
- Link to detail page.

3. `/prompts/[promptKey]`
- Fetch prompt detail with versions and active pointer.
- Draft form:
- content
- variables_schema (JSON textarea)
- created_by
- Publish action:
- env selector (dev/stg/prod)
- POST publish API
- Rollback action:
- target version
- POST rollback API

4. `/publish-history`
- Fetch publish events and deliveries.
- Show status table for monitoring.

## Component Plan
- `PromptListTable`
- `DraftEditorForm`
- `PublishForm`
- `RollbackForm`
- `DeliveryTable`

## Error Handling
- Render API errors inline on each page.
- JSON parse failures for schema should be surfaced before submission.

## Run/Env
- `NEXT_PUBLIC_API_BASE_URL` required.
- Default local backend: `http://localhost:8000`.
