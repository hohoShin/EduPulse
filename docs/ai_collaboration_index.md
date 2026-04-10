# AI 협업 문서 인덱스

본 프로젝트는 AI 코딩 에이전트(Claude Code + oh-my-claudecode)와의 협업을 통해 개발되었습니다.
기획, 설계, 구현, 검증, 배포 전 과정에서 AI가 공동 의사결정자로 참여하였으며, 그 기록이 아래 문서들에 정리되어 있습니다.

---

## AI 활용 리포트 (`docs/ai_reports/`)

프로젝트 전 과정의 AI 활용을 단계별로 기록한 공식 리포트입니다.

| # | 리포트 | 주제 |
|---|--------|------|
| 1 | [아이디어 기획](ai_reports/AI_활용_리포트_1_아이디어_기획.md) | Claude 대화로 아이디어 발굴, 서비스 범위 설계, 기술 환경 결정 |
| 2 | [Ralplan 계획 수립](ai_reports/AI_활용_리포트_2_OMC_계획수립.md) | Planner-Architect-Critic 합의 기반 MVP 4-Phase 계획 |
| 3 | [OMC 도구별 활용 전략](ai_reports/AI_활용_리포트_3_OMC_도구별_활용전략.md) | 에이전트 페르소나, 모델 라우팅, 토큰 최적화 전략 |
| 4 | [모델 성능 개선](ai_reports/AI_활용_리포트_4_모델_성능_개선.md) | 주간 데이터 전환 + 분야별 분리 + LSTM 증강으로 MAPE 개선 |
| 5 | [프론트엔드 개발](ai_reports/AI_활용_리포트_5_프론트엔드_개발.md) | React 5페이지 구현 + UX 고도화 + Docker 빌드 |
| 6 | [서버 배포](ai_reports/AI_활용_리포트_6_서버_배포.md) | 20건 이슈 수정 + DigitalOcean Portainer 배포 |
| 7 | [종합 요약](ai_reports/AI_활용_리포트_7_종합_요약.md) | 전체 AI 협업 과정 분석 및 정량적 성과 |
| - | [모델 전체 해설](ai_reports/EduPulse_모델_전체_해설.md) | 데이터-전처리-모델-API 파이프라인 상세 해설 (학습용) |

---

## 기획 및 설계 문서 (`.omc/plans/`)

AI와 함께 작성한 시스템 설계 및 구현 계획서입니다.

| 문서 | 설명 |
|---|---|
| [edupulse-full-build.md](../.omc/plans/edupulse-full-build.md) | MVP 전체 구현 계획서 (Architect/Critic 피드백 반영) |
| [edupulse-backend.md](../.omc/plans/edupulse-backend.md) | 백엔드 API 설계 (FastAPI, DB, 모델 서빙) |
| [edupulse-frontend.md](../.omc/plans/edupulse-frontend.md) | 프론트엔드 아키텍처 설계 (React, 컴포넌트 구조) |
| [frontend-plan.md](../.omc/plans/frontend-plan.md) | 프론트엔드 상세 구현 계획 |
| [frontend-mockup-3pages.md](../.omc/plans/frontend-mockup-3pages.md) | 3개 페이지 목업 설계 |
| [frontend-enhancement-v2.md](../.omc/plans/frontend-enhancement-v2.md) | 프론트엔드 UX 개선 18항목 |
| [lstm-data-improvement.md](../.omc/plans/lstm-data-improvement.md) | LSTM 데이터 파이프라인 개선 |
| [search-volume-collectors.md](../.omc/plans/search-volume-collectors.md) | 검색량 수집기 설계 (Naver/Google) |
| [expand-synthetic-data-generators.md](../.omc/plans/expand-synthetic-data-generators.md) | 합성 데이터 생성기 확장 |
| [server-deploy-fixes.md](../.omc/plans/server-deploy-fixes.md) | 서버 배포 전 이슈 수정 (CRITICAL 6 + HIGH 8) |
| [open-questions.md](../.omc/plans/open-questions.md) | 미결 설계 질문 및 결정 사항 |

## 팀 에이전트 이관 문서 (`.omc/handoffs/`)

멀티 에이전트 팀 실행 시 단계 간 이관(handoff) 기록입니다.

| 문서 | 설명 |
|---|---|
| [team-plan-to-exec.md](../.omc/handoffs/team-plan-to-exec.md) | 기획 → 실행 이관 (결정/기각/리스크) |
| [team-exec-phase1-to-phase2.md](../.omc/handoffs/team-exec-phase1-to-phase2.md) | 실행 Phase 1 → Phase 2 이관 |
| [team-exec-phase2-to-phase3+4.md](../.omc/handoffs/team-exec-phase2-to-phase3+4.md) | 실행 Phase 2 → Phase 3+4 이관 |

## 프론트엔드 개발 과정 기록 (`.sisyphus/`)

반복 실행 루프(ralph) 중 발생한 문제, 의사결정, 학습 내용입니다.

### 분석 및 기획
| 문서 | 설명 |
|---|---|
| [edupulse-frontend-phase-a.md](../.sisyphus/plans/edupulse-frontend-phase-a.md) | 프론트엔드 Phase A 계획 |
| [edupulse-frontend-replan.md](../.sisyphus/plans/edupulse-frontend-replan.md) | 프론트엔드 재계획 |
| [frontend-ui-ux-improvements.md](../.sisyphus/plans/frontend-ui-ux-improvements.md) | UI/UX 개선 계획 |

### 의사결정 및 문제 해결
| 문서 | 설명 |
|---|---|
| [decisions.md](../.sisyphus/notepads/edupulse-frontend-phase-a/decisions.md) | 주요 의사결정 기록 |
| [issues.md](../.sisyphus/notepads/edupulse-frontend-phase-a/issues.md) | 이슈 트래킹 (scope creep, React 버전 등) |
| [learnings.md](../.sisyphus/notepads/edupulse-frontend-phase-a/learnings.md) | 학습 내용 |

### 검증 및 증거
| 문서 | 설명 |
|---|---|
| [task-3-adapter-seams.md](../.sisyphus/evidence/task-3-adapter-seams.md) | Adapter 패턴 구현 검증 증거 |
| [REPAIR_LOG.md](../.sisyphus/notepads/final-wave-review/REPAIR_LOG.md) | 최종 리뷰 lint 수정 로그 |

## 초기 기획 문서 (`docs/ai_plans/`)

| 문서 | 설명 |
|---|---|
| [edupulse-full-build.md](ai_plans/edupulse-full-build.md) | 초기 MVP 구현 계획 (Ralplan 합의 전) |
| [edupulse-backend.md](ai_plans/edupulse-backend.md) | 초기 백엔드 설계 |
| [edupulse-frontend.md](ai_plans/edupulse-frontend.md) | 초기 프론트엔드 설계 |
| [edupulse-frontend-phases.md](ai_plans/edupulse-frontend-phases.md) | 프론트엔드 Phase 분리 계획 |
