# AI 활용 리포트 2 — Ralplan 합의 기반 프로젝트 계획 수립

> **작성일:** 2026-04-08
> **사용 도구:** Claude Code (Claude Opus 4.6) + oh-my-claudecode Ralplan
> **목적:** AI 멀티에이전트 합의 워크플로우를 활용한 EduPulse 구현 계획 수립 과정 기록

---

## 1. 배경

EduPulse 프로젝트의 README.md와 CLAUDE.md에 아키텍처, 기술 스택, 디렉토리 구조가 정의된 상태에서 실제 구현 계획을 수립해야 했다. 프로젝트는 greenfield 상태로, 14줄짜리 FastAPI Hello World(`main.py`)만 존재했다.

**제약 조건:**
- 공모전 데드라인: 2주 이내
- 개발 인원: 2인
- 서버 사양: DigitalOcean Droplet 1vCPU / 2GB RAM
- 실제 학원 데이터 없음 (합성 데이터 필요)

---

## 2. Ralplan 워크플로우 개요

Ralplan은 3개의 AI 에이전트(Planner, Architect, Critic)가 합의에 도달할 때까지 계획을 반복 검토하는 멀티에이전트 워크플로우이다.

```
[Planner] → 초안 작성
    ↓
[Architect] → 아키텍처 리뷰 + Steelman 반론
    ↓
[Critic] → 품질 기준 평가 (5항목)
    ↓
  판정: APPROVE → 실행 착수
        ITERATE → Planner가 피드백 반영 후 재순환
        REJECT  → 전면 재설계
```

### 품질 평가 기준 (Critic)

| 기준 | 설명 |
|---|---|
| 원칙-옵션 일관성 | 명시한 원칙과 선택한 옵션이 정합하는가? |
| 대안 공정 평가 | 대안이 실질적 장단점과 함께 검토되었는가? |
| 리스크 완화 명확성 | 리스크별 구체적 완화 전략이 있는가? |
| 검증 가능한 수락 기준 | 각 Phase 완료를 객관적으로 확인 가능한가? |
| 구체적 검증 절차 | 실행 가능한 명령어/체크리스트가 있는가? |

---

## 3. Iteration 1 — 초안 및 피드백

### 3.1 Planner 초안 (v1)

**선택한 전략:** Contract-First Parallel (Option B)
- 6 Phase 구조: Foundation → Data → Modeling → API → Frontend → DevOps
- 3개 모델(Prophet, LSTM, XGBoost) 전체 구현
- 예상 기간: 12-16일

**RALPLAN-DR 요약:**
- 원칙 5개: Data-First, Incremental Vertical Slices, Contract-Driven Integration, Time-Series Integrity, Environment-Aware Design
- 핵심 결정 요인: 공모전 데드라인, 데이터 부재, 서버 제약

### 3.2 Architect 리뷰 — ITERATE 판정

**Steelman 반론 (가장 강력한 반대 논거):**

> "합성 데이터 위에 3개 모델을 학습시키는 것은 기술적 깊이가 아니라 기술적 허상이다. 생성자가 심어놓은 패턴을 모델이 재발견하는 자기순환 구조이므로, MAPE 수치는 모델 성능이 아니라 합성 데이터 설계 품질을 반영할 뿐이다."

**주요 지적 사항:**

1. **1인/다인 개발 여부가 미확정** — 계획의 핵심 장점(병렬화)이 1인 작업 시 완전 무효화됨
2. **requirements.txt 환경 미분리** — Droplet(2GB)에 torch+jupyter+selenium 전체 설치 시 메모리 초과
3. **Droplet 메모리 예산 미명시** — PostgreSQL(300MB) + FastAPI(100MB) + 3모델(~1.2GB) = 2GB 초과
4. **디렉토리 구조 불일치** — `edupulse/` 패키지와 CLAUDE.md 구조 간 import 관계 불명확
5. **APScheduler 리스크** — API 프로세스 내 재학습 시 응답 블로킹

**Tradeoff Tension:**
- "Contract-First 병렬화"와 "1인 개발 현실" 사이의 미해소 긴장

### 3.3 Critic 리뷰 — ITERATE 판정

**추가 발견 사항:**

1. **기존 `main.py` → `api/main.py` 마이그레이션 계획 누락** — Phase 1 시작 5분 만에 멈추는 블로커
2. **`pydantic-settings` 패키지 누락** — Pydantic v2에서 `BaseSettings`는 별도 패키지. ImportError 발생
3. **대안이 2개뿐** — MVP-First(Option C) 검토 부재
4. **`edupulse/models/`(ORM) vs `model/`(ML) 명명 혼동** 가능성
5. **Frontend 기술 선택 미명시** — Vite? CRA? 패키지 매니저?

**미통과 품질 기준:**
- 대안 공정 평가: FAIL (2개 옵션만 비교)
- 원칙-옵션 일관성: PARTIAL (Environment-Aware 원칙 위반)

---

## 4. Open Questions 해결

Iteration 1 이후, 사용자와의 Q&A를 통해 7개 미결 질문을 해결했다.

| 질문 | 결정 | 영향 |
|---|---|---|
| 개발 인원 | **2인** | Backend/Frontend 병렬 가능 |
| 공모전 데드라인 | **2주 이내** | MVP-First 전략 필수 |
| 수요 등급 임계값 | **전체 통일** (25/12명) | 구현 단순화 |
| API 키 | **네이버 무료 발급 가능**, pytrends 무료 | 실제 수집 모듈 구현 가능 |
| 로컬 DB | **PostgreSQL (Docker)** | 프로덕션과 동일 환경 |
| MLflow | **2주 데드라인에서 제외** | requirements에서 제거 |

---

## 5. Iteration 2 — 수정 및 합의

### 5.1 Planner 수정 (v2)

**전략 변경:** Contract-First Parallel (Option B) → **MVP-First (Option C)**

| 항목 | v1 | v2 |
|---|---|---|
| Phase 수 | 6 | **4** |
| 모델 전략 | 3모델 전체 구현 | **XGBoost primary**, Prophet/LSTM stretch |
| 기간 | 12-16일 | **10일 + 2일 버퍼** |
| Frontend | React 3페이지 풀 구현 | **Dashboard + Simulator MVP** |
| 스케줄러 | APScheduler | **cron** |
| ORM 디렉토리 | `edupulse/models/` | **`edupulse/db_models/`** (혼동 방지) |

**수정된 4 Phase 구조:**

```
Phase 1 (Day 1-2)  : Foundation — 프로젝트 구조, 스키마 계약, DB, Frontend 초기화
Phase 2 (Day 3-6)  : Data + Model — 합성 데이터, 전처리, XGBoost 학습
Phase 3 (Day 6-8)  : API + Frontend — 라우터 구현, Frontend-API 연결
Phase 4 (Day 9-10) : Polish — Docker, 재학습 스크립트, 문서화
Buffer  (Day 11-12): Prophet 추가 / 버그 수정 / 발표 준비
```

**Droplet 메모리 예산 (신규):**

| 컴포넌트 | 메모리 (MB) |
|---|---|
| OS + 시스템 | ~200 |
| PostgreSQL | ~300 |
| FastAPI (uvicorn) | ~100 |
| XGBoost 모델 | ~50 |
| Python 런타임 | ~150 |
| **합계** | **~800** |
| **여유** | **~1200** |

### 5.2 Architect 재검토 — APPROVE (조건부)

**이전 12개 이슈 중 11개 해소, 1개 사소한 모순 잔존.**

- 조건: `apscheduler` 의존성 제거 (cron 결정과 모순)
- 권고: Phase 2에서 Prophet 최소 학습을 soft stretch target으로 추가 검토

**Steelman 반론 (약화됨):**
> "XGBoost 단일 모델에 올인하면 공모전에서 모델 다양성 부족으로 보일 수 있다. Prophet은 학습 비용이 매우 낮으므로(3-10분) 함께 학습시키면 안전장치가 된다."

→ 반론은 유효하나, MVP-First 원칙 내에서 stretch goal로 이미 포함되어 있으므로 계획 변경 불필요.

### 5.3 Critic 재평가 — APPROVE (조건부)

**5개 품질 기준 전부 Pass.**

| 기준 | v1 | v2 |
|---|---|---|
| 원칙-옵션 일관성 | PARTIAL | **Pass** |
| 대안 공정 평가 | FAIL | **Pass** |
| 리스크 완화 명확성 | PARTIAL | **Pass** |
| 검증 가능한 수락 기준 | PARTIAL | **Pass** |
| 구체적 검증 절차 | PARTIAL | **Pass** |

- 조건: Architect와 동일 (apscheduler 제거)
- 권고: statsmodels/selenium 의도적 제거 주석, Follow-ups에 Alembic 추가

---

## 6. 최종 산출물

| 산출물 | 설명 |
|---|---|
| `edupulse-full-build.md` | MVP 구현 계획서 v2 (4 Phase, 2주, 2인) |
| `frontend-plan.md` | Frontend 상세 구현 계획 (Person B 전용) |
| `open-questions.md` | 미결 질문 18개 전부 해결 |

---

## 7. AI 활용 효과 분석

### 워크플로우 가치

| 관점 | 효과 |
|---|---|
| **리스크 조기 발견** | Architect가 Droplet 메모리 초과(3모델 동시 서빙 불가)를 계획 단계에서 발견. 구현 후 발견했다면 아키텍처 재설계 필요 |
| **품질 기준 강제** | Critic이 "대안 2개만 비교"를 FAIL 판정 → MVP-First(Option C) 추가로 최적 전략 발견 |
| **자기순환 방지** | Architect의 steelman 반론이 "합성 데이터 3모델 비교의 허구성"을 지적 → 단일 모델 집중으로 전략 전환 |
| **구체성 확보** | Critic이 "수락 기준이 주관적"을 지적 → 모든 Phase에 bash 커맨드 기반 검증 절차 추가 |
| **누락 방지** | `pydantic-settings` 누락, `main.py` 마이그레이션 미계획 등 실행 시 즉시 막히는 블로커를 사전 발견 |

### 반복 효율

- **Iteration 1:** 초안 작성 + 2개 에이전트 리뷰 → 15개 이슈 발견
- **Iteration 2:** 피드백 반영 + 재검토 → 14/15 해소, 1개 사소한 모순만 잔존
- **합의 도달:** 2회 반복으로 APPROVE

### 한계점

1. **합성 데이터 자기순환 문제**는 AI 에이전트가 지적할 수는 있지만 해결할 수는 없다. 실제 데이터 없이는 모델 성능 검증이 원천적으로 불가능하다.
2. **일정 추정의 정확도**는 검증되지 않았다. "Day 5에 XGBoost 학습 완료"가 실제로 달성 가능한지는 구현 단계에서만 확인 가능하다.
3. **공모전 심사 기준과의 정합성**은 에이전트가 판단할 수 없다. 심사위원의 평가 기준에 따라 "1개 모델 깊이 있게" vs "3개 모델 폭넓게"의 최적 전략이 달라진다.
