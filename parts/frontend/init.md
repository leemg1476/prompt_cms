# Frontend init.md

## 목표
- 운영자가 프롬프트를 검색, 편집, 배포(Publish), 롤백할 수 있는 CMS UI 제공
- 배포 결과(Agent Push 성공/실패)를 화면에서 즉시 확인

## 기술 스택
- Next.js (App Router) + React + TypeScript
- TanStack Query
- Monaco Editor
- Tailwind CSS + shadcn/ui
- React Hook Form + Zod

## 핵심 페이지
1. `/prompts`
- 프롬프트 목록, 검색, 필터(환경/팀/상태)

2. `/prompts/[promptKey]`
- 현재 active 버전 확인
- Draft 편집/저장
- 버전 Diff
- 테스트 렌더(샘플 context 입력)

3. `/publish-history`
- publish_events 목록
- push_deliveries 상태(success/pending/failed)
- 실패 원인(last_error) 조회

## UX 규칙
- Draft 미저장 변경이 있으면 이탈 확인 모달 표시
- Publish 버튼 활성화 조건
- 필수 항목 입력 완료
- schema 검증 통과
- 테스트 통과(옵션으로 강제)
- Publish 이후 delivery 상태 폴링(5~10초)

## 연동 API
- GET `/api/prompts`
- GET `/api/prompts/{prompt_key}`
- POST `/api/prompts/{prompt_key}/draft`
- POST `/api/prompts/{prompt_key}/publish?env={dev|stg|prod}`
- POST `/api/prompts/{prompt_key}/rollback?env={env}&to_version={n}`
- GET `/api/publish-events?prompt_key={key}`

## 권한
- `viewer`: 조회만 가능
- `editor`: draft 저장 가능
- `publisher`: publish/rollback 가능
