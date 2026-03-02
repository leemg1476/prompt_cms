# Prompt CMS

Prompt CMS sample implementation with:
- Frontend: Next.js
- Backend: FastAPI
- Agent: FastAPI + LangGraph (test runtime)
- DB: PostgreSQL

## Structure
- `docs/implementation/frontend.md`
- `docs/implementation/backend.md`
- `docs/implementation/db.md`
- `frontend/`
- `backend/`
- `agent/`
- `db/init.sql`
- `docker-compose.yml`

## Test First (Recommended)
Run from `backend/`:
1. `python -m venv .venv`
2. `.\\.venv\\Scripts\\activate`
3. `pip install -r requirements-dev.txt`
4. `pytest -m unit`

Use Docker after unit tests pass, for service-level integration checks.

## Run with Docker (Integration Phase)
1. `docker compose up --build`
2. Frontend: `http://localhost:3000`
3. Backend: `http://localhost:8000/docs`
4. Agent: `http://localhost:8010/docs`
5. Health:
- Backend: `http://localhost:8000/health`
- Agent: `http://localhost:8010/health`

## Local Run (without Docker)

### DB
- Run PostgreSQL and create `prompt_cms` database.
- Apply schema with `db/init.sql`.

### Backend
1. `cd backend`
2. `python -m venv .venv`
3. `.\\.venv\\Scripts\\activate`
4. `pip install -r requirements.txt`
5. Set env:
- `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/prompt_cms`
- `PUSH_AUTH_TOKEN=local-dev-token`
6. `uvicorn app.main:app --reload`

### Frontend
1. `cd frontend`
2. `npm install`
3. `set NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
4. `npm run dev`

### Agent (LangGraph test server)
1. `cd agent`
2. `python -m venv .venv`
3. `.\\.venv\\Scripts\\activate`
4. `pip install -r requirements-dev.txt`
5. `uvicorn app.main:app --reload --port 8010`

## Minimal Flow
1. Open `/prompts`
2. Open a prompt key and save draft
3. Publish latest draft
4. Open `/publish-history`
5. Run `Run Worker Once` button to dispatch pending deliveries
6. Verify agent cache:
- `GET http://localhost:8010/internal/prompts/cache`
7. Run agent:
- `POST http://localhost:8010/api/agent/run`
