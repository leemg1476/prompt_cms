# init.md - Prompt CMS 간소화 설계

이 문서는 프로젝트를 `Frontend / Backend / DB` 3개 파트로 나눠 정의한다.

## 1) Frontend (React + Next.js)

### 목표
- 프롬프트 생성/수정/배포/롤백을 운영자가 빠르게 처리
- 배포 후 Agent 반영 상태를 화면에서 추적

### 기술
- Next.js(App Router), React, TypeScript
- TanStack Query, Monaco Editor
- Tailwind CSS, shadcn/ui

### 주요 기능
- Prompt 목록/검색/필터
- Prompt 상세(현재 active, 버전 히스토리)
- Draft 편집/저장
- Diff 비교
- Publish(dev/stg/prod)
- Rollback(to_version)
- 테스트 렌더(샘플 context)
- Publish delivery 상태(success/pending/failed)

### UX 규칙
- 미저장 이탈 방지
- Schema 검증 통과 시 Publish 가능
- Publish 후 상태 폴링으로 결과 표시

## 2) Backend (FastAPI + LangGraph)

### 목표
- CMS API와 Push Worker, Agent Runtime을 분리해 안정적으로 운영
- 프롬프트를 재배포 없이 런타임 반영

### 서비스 구성
1. CMS API (FastAPI)
- Prompt CRUD
- Publish/Rollback
- Agent Registry/Subscription

2. Push Worker
- pending delivery 처리
- 실패 재시도(지수 백오프)

3. Agent Runtime (FastAPI + LangGraph)
- POST /internal/prompts/push 수신
- PromptStore 캐시 갱신
- LangGraph 노드에서 prompt_store.render() 사용

### Publish 처리 원칙
- 트랜잭션 내: active 전환 + publish_event + push_deliveries 생성
- 트랜잭션 외: worker가 실제 push 호출

### Push 규약
- Header: Authorization, Idempotency-Key
- Body: prompt_key, version, checksum, content, variables_schema
- 응답: ok, applied, cache_state

### 재시도 정책
- 5xx/timeout: 1m -> 2m -> 5m -> 10m -> 30m -> 1h (max 24h)
- 4xx: 즉시 failed

## 3) DB (PostgreSQL)

### 목표
- 버전 관리, 감사 로그, push 전달 상태를 일관되게 저장

### 핵심 테이블
- prompts
- prompt_versions
- prompt_active_pointer
- agent_registry
- prompt_subscriptions
- publish_events
- push_deliveries

### 필수 제약/인덱스
- unique: prompts(prompt_key)
- unique: prompt_versions(prompt_id, version)
- unique: prompt_subscriptions(prompt_id, agent_id)
- unique: push_deliveries(publish_event_id, agent_id)
- index: prompt_versions(prompt_id, status)
- index: agent_registry(environment, is_enabled)
- index: push_deliveries(status, next_retry_at)

### 운영 기준
- UTC 저장, 표시 시 로컬 타임존 변환
- Alembic으로 스키마 관리
- PITR 백업 및 감사 로그 장기 보관

## 구현 순서
1. DB 스키마/마이그레이션
2. Backend API/Worker/Agent push 구현
3. Frontend 화면/연동 구현
4. 통합 테스트(Publish -> Push -> Agent 반영)
