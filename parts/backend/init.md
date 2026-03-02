# Backend init.md

## 목표
- CMS API, Publish 트랜잭션, Push Worker, Agent 연동을 안정적으로 제공
- FastAPI + LangGraph 환경에서 프롬프트를 런타임 교체 가능하게 구성

## 서비스 구성
1. `cms-api` (FastAPI)
- Prompt CRUD
- Publish/Rollback API
- Agent Registry/Subscription 관리

2. `push-worker`
- outbox(`push_deliveries`) 처리
- 재시도/백오프/실패 기록

3. `agent-runtime` (FastAPI + LangGraph)
- `/internal/prompts/push` 수신
- PromptStore 캐시 갱신
- LangGraph 노드에서 `prompt_store.render()` 사용

## 기술 스택
- Python 3.12+
- FastAPI
- SQLAlchemy 2.0 + Alembic
- Pydantic v2
- httpx
- Redis(큐/락/idempotency)

## CMS 핵심 플로우
1. Draft 저장
- content checksum(SHA256) 계산
- status=draft로 저장

2. Publish
- 트랜잭션 내부
- draft -> active 전환
- active pointer 갱신
- publish_event 생성
- agent별 push_delivery(pending) 생성
- 트랜잭션 외부
- worker가 실제 push 수행

3. Rollback
- 특정 버전을 active로 승격
- publish와 동일하게 event/delivery 생성

## Push Worker 정책
- 처리 대상: `status=pending AND next_retry_at <= now()`
- 성공 기준: HTTP 200 + body.ok=true
- 재시도: 5xx/timeout (지수 백오프)
- 1m -> 2m -> 5m -> 10m -> 30m -> 1h (최대 24h)
- 4xx는 즉시 failed

## Agent Push 규약
- Endpoint: POST `/internal/prompts/push`
- Header: `Authorization`, `Idempotency-Key`
- Body: prompt_key, version, checksum, content, variables_schema
- 처리 순서
1. idempotency 검사
2. checksum 비교
3. cache upsert
4. 응답(ok/applied/cache_state)

## 테스트 범위
- 단위 테스트: publish service, retry policy, prompt_store
- 통합 테스트: publish -> worker -> agent push
- E2E: UI publish 후 실제 응답 품질 변화 확인
