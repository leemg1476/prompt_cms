# DB init.md

## 목표
- 프롬프트 버전 관리, 배포 이벤트, push 전달 상태를 일관되게 저장
- 운영/감사/재시도 요구사항을 Postgres에서 충족

## 기술 기준
- PostgreSQL 16+
- UTF-8
- UTC 저장(화면 표시 시 KST 변환)
- Alembic 마이그레이션

## 핵심 테이블
1. `prompts`
- prompt_key 유니크, 설명/소유팀 관리

2. `prompt_versions`
- 버전별 본문, checksum, status(draft/active/archived), variables_schema

3. `prompt_active_pointer`
- prompt별 현재 active version 포인터

4. `agent_registry`
- 환경(dev/stg/prod)별 agent endpoint/인증 참조

5. `prompt_subscriptions`
- prompt <-> agent 매핑

6. `publish_events`
- publish/rollback 감사 이력

7. `push_deliveries`
- agent별 push 결과, 시도 횟수, 실패 사유, 다음 재시도 시각

## 필수 제약/인덱스
- unique: `prompts(prompt_key)`
- unique: `prompt_versions(prompt_id, version)`
- unique: `prompt_subscriptions(prompt_id, agent_id)`
- unique: `push_deliveries(publish_event_id, agent_id)`
- index: `prompt_versions(prompt_id, status)`
- index: `agent_registry(environment, is_enabled)`
- index: `push_deliveries(status, next_retry_at)`

## 무결성 규칙
- prompt당 active는 1개만 유지
- publish_event 생성 없이 active 변경 금지
- publish_event 생성 시 구독 대상 push_delivery 동시 생성
- 상태 전이: pending -> success|failed|pending(retry)

## 운영 정책
- PITR 활성화
- `publish_events`, `push_deliveries` 최소 1년 보관
- 장기 운영 시 월 단위 파티셔닝 검토

## 보안
- 앱/워커/읽기 전용 DB 계정 분리
- 최소 권한 원칙 적용
- 민감값은 DB에 평문 저장하지 않고 secret ref만 저장
