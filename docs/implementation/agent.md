# Agent Detailed Implementation Plan

## Scope
- FastAPI 기반 테스트용 LangGraph runtime 제공
- CMS Push payload를 받아 prompt cache 업데이트
- 테스트 실행용 agent run endpoint 제공

## Endpoints
- `GET /health`
- `POST /internal/prompts/push`
- `GET /internal/prompts/cache`
- `POST /api/agent/run`

## Runtime Design
- `PromptStore` in-memory cache
- `Idempotency-Key` in-memory set
- LangGraph single-node workflow:
- state: `prompt_key`, `user_input`, `output`
- node: cache prompt + user input 결합 응답 생성

## Test Coverage
- push -> cache update
- idempotency validation
- run endpoint with bootstrapped/default prompt
