# Agent Detailed Implementation Plan

## Scope
- FastAPI 기반 테스트용 LangGraph runtime 제공
- CMS Push payload를 받아 prompt cache 업데이트
- Push payload를 YAML 파일로 저장 후 YAML 재로딩으로 cache 업데이트
- 테스트 실행용 agent run endpoint 제공
- Streamlit 기반 테스트 UI 제공
- LangSmith 추적 옵션을 환경변수로 제어

## Endpoints
- `GET /health`
- `POST /internal/prompts/push`
- `GET /internal/prompts/cache`
- `GET /internal/prompts/files`
- `POST /api/agent/run`
- `GET /api/agent/tracing`

## Runtime Design
- `PromptStore` in-memory cache
- `PromptStore` YAML 디렉터리(`PROMPT_YAML_DIR`) 기반 파일 관리
- `Idempotency-Key` in-memory set
- LangGraph single-node workflow:
- state: `prompt_key`, `user_input`, `output`
- node: cache prompt + user input 결합 응답 생성
- Streamlit UI:
- Agent run with trace fields
- Cache/files 조회
- Backend publish helper

## Test Coverage
- push -> cache update
- push -> yaml file write -> yaml reload -> cache update
- idempotency validation
- run endpoint with bootstrapped/default prompt
- tracing status endpoint and run-level trace options
