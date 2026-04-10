# AI 활용 리포트 6 — 서버 배포 및 인프라 구성

> **작성일:** 2026-04-10
> **사용 도구:** Claude Code (Claude Opus 4.6) + oh-my-claudecode
> **목적:** DigitalOcean Droplet 배포 과정에서 발견된 이슈 20건의 AI 기반 진단 및 수정 기록

---

## 1. 배경

EduPulse의 로컬 개발 환경(M4 MacBook)에서 정상 동작하던 코드를 DigitalOcean Droplet에 배포하는 과정에서 다수의 이슈가 발생하였다.

**배포 인프라:**

| 항목 | 내용 |
|------|------|
| 서버 | DigitalOcean Droplet 1 vCPU / 2GB RAM |
| 배포 방식 | Portainer (Docker Compose 스택 배포) + Nginx Proxy Manager |
| 컨테이너 구성 | db(PostgreSQL) + api(FastAPI) + frontend(React + nginx) |
| 로컬 환경 | M4 MacBook (MPS, Python 3.12, 개발/실험/LSTM 학습) |

**핵심 문제:** 로컬에서는 상대 경로, localhost, 풍부한 메모리(16GB+) 등 관대한 환경에서 동작하던 코드가 Docker 컨테이너 내부(WORKDIR=/app)와 1 vCPU / 2GB RAM 제약 아래에서 다수의 장애를 일으켰다. 배포 전에 이러한 이슈를 체계적으로 식별하고 수정할 필요가 있었다.

---

## 2. AI 기반 이슈 진단 — 20건 분류

AI(Architect + Code-Reviewer)가 배포 전 코드베이스를 전수 검사하여 **20건의 이슈**를 발견하였다. 심각도는 3단계로 분류하였다.

| 심각도 | 건수 | 기준 |
|--------|------|------|
| **CRITICAL** | 6건 | 배포 자체가 불가능하거나 컨테이너 기동 실패 |
| **HIGH** | 8건 | 기동은 되지만 안정성/보안에 심각한 위험 |
| **MEDIUM** | 6건 | 기능상 문제는 없으나 운영 품질 개선 필요 |

### 2.1 Phase 1: CRITICAL — 배포 차단 이슈 (6건)

| # | 이슈 | 원인 | 수정 내용 |
|---|------|------|-----------|
| 1.1 | Dockerfile Python 버전 불일치 | Python 3.11에서 3.12로 학습된 LSTM pickle 로드 실패 | `python:3.11-slim` → `python:3.12-slim` |
| 1.2 | 상대 경로 전면 실패 | Docker WORKDIR=/app에서 `../../data/raw/` 등 상대 경로 불일치 | `PROJECT_ROOT` 기반 절대 경로로 통일 (`constants.py`) |
| 1.3 | CORS localhost 하드코딩 | Droplet IP/도메인에서 프론트엔드 요청이 차단됨 | 환경변수 `CORS_ORIGINS` 기반으로 변경 |
| 1.4 | DB 크레덴셜 평문 노출 | `docker-compose.yml`에 비밀번호가 직접 기재 | 환경변수 `POSTGRES_PASSWORD`로 치환 |
| 1.5 | 글로벌 예외 핸들러 부재 | 미처리 예외 시 Python traceback이 클라이언트에 노출 | FastAPI 글로벌 예외 핸들러 추가 (traceback 로깅만, 클라이언트에는 500 응답) |
| 1.6 | deploy.sh 문법 오류 | `docker-compose` v1 문법 + Alembic 마이그레이션 누락 | `docker compose` v2 문법 + 마이그레이션 단계 추가 |

### 2.2 Phase 2: HIGH — 안정성/보안 (8건)

| # | 이슈 | 수정 내용 |
|---|------|-----------|
| 2.1 | XGBoost `n_jobs=-1` | 1 vCPU에서 `n_jobs=-1`은 무의미하며 스레드 경합 유발 → `n_jobs=1` 고정 |
| 2.2 | `torch.load()` 보안 취약점 | 임의 코드 실행 가능 → `weights_only=True` 파라미터 추가 |
| 2.3 | CSV 비캐싱 읽기 5건 | 동일 CSV를 매 요청마다 `pd.read_csv()` → `load_csv_cached()` 통일 |
| 2.4 | DB 커넥션 풀 무제한 | 2GB RAM에서 커넥션 폭증 시 OOM → `pool_size=3, max_overflow=2` 제한 |
| 2.5 | 모델 프리로딩 silent except | 로딩 실패를 무시하여 디버깅 불가 → `logger.warning()` 추가 |
| 2.6 | `.dockerignore` 미비 | `frontend/`, `tests/`, `.env` 등이 이미지에 포함 → `.dockerignore` 보완 |
| 2.7 | 동시 모델 로딩 방어 부재 | 동시 요청으로 모델 2중 로딩 시 OOM → per-model `threading.Lock` 추가 |
| 2.8 | Ensemble confidence 역전 | 앙상블 가중치 합산 시 confidence가 개별 모델보다 낮아지는 경우 발생 → 역전 방지 로직 |

### 2.3 Phase 3: MEDIUM — 개선사항 (6건)

| # | 이슈 | 수정 내용 |
|---|------|-----------|
| 3.1 | LSTM 프리로딩 불필요 | API에서 LSTM 모델 선택 불가 + ~200MB RAM 점유 → 프리로딩 제거 |
| 3.2 | CSV 캐시 갱신 미지원 | 파일 변경 시 재시작 필요 → mtime 기반 자동 갱신 |
| 3.3 | `requirements-server.txt` 미분리 | Droplet에 jupyter, plotly 등 불필요한 패키지 설치 → 서버 전용 파일 독립화 |
| 3.4 | Uvicorn 기본 설정 | 프로덕션 튜닝 부재 → `timeout-keep-alive=5`, `limit-concurrency=10` |
| 3.5 | Docker 리소스 제한 없음 | 컨테이너 간 메모리 경합 가능 → api: 1024M, db: 512M 제한 |
| 3.6 | `docker-compose.dev.yml` version 키 | Docker Compose v2에서 deprecated 경고 → version 키 제거 |

---

## 3. 수정 과정

### 3.1 실행 전략

수정은 심각도 순서대로 Phase 단위로 진행하였다. 각 Phase 완료 후 전체 테스트를 통과시킨 뒤 다음 Phase로 진행하였다.

```
Phase 1 (CRITICAL) → 테스트 통과 확인
    ↓
Phase 2 (HIGH)     → 테스트 통과 확인
    ↓
Phase 3 (MEDIUM)   → 테스트 통과 확인 → 최종 검증
```

### 3.2 Phase 1 내부 의존관계 분석

AI가 Phase 1의 6건 이슈 간 의존관계를 분석하여 수정 순서를 자동 도출하였다.

```
[1.2 경로 통일] ─── 먼저 (다른 수정의 기반)
       │
       ├── [1.3 CORS 환경변수화]     ── 병렬 가능
       └── [1.5 글로벌 예외 핸들러]   ── 병렬 가능
              │
              ▼
       [1.4 DB 크레덴셜 환경변수화]
              │
              ▼
       [1.1 Dockerfile Python 3.12]
              │
              ▼
       [1.6 deploy.sh 문법 수정]      ── 마지막 (Dockerfile 의존)
```

**근거:** 경로 통일(1.2)이 `constants.py`를 수정하며, 이후 CORS(1.3)와 예외 핸들러(1.5)는 독립적인 파일을 수정하므로 병렬 진행이 가능하다. Dockerfile(1.1)은 경로와 크레덴셜이 모두 반영된 뒤 빌드해야 하므로 후순위이며, deploy.sh(1.6)는 Dockerfile에 의존한다.

### 3.3 주요 수정 코드

#### 경로 통일 (`constants.py`)

```python
# 변경 전: 각 모듈에서 상대 경로 사용
DATA_DIR = "../../data/raw/"

# 변경 후: PROJECT_ROOT 기반 절대 경로
import pathlib
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_SAVED_DIR = PROJECT_ROOT / "model" / "saved"
```

#### CORS 환경변수화 (`middleware.py`)

```python
# 변경 전
origins = ["http://localhost:3000", "http://localhost:5173"]

# 변경 후
import os
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
```

#### 글로벌 예외 핸들러 (`main.py`)

```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```

---

## 4. Droplet 메모리 예산

2GB RAM 제약에서 각 컴포넌트의 메모리 사용량을 분석하여 배포 가능 여부를 사전 검증하였다.

| 컴포넌트 | 메모리 (MB) |
|----------|------------|
| OS + 시스템 | ~200 |
| PostgreSQL | ~300 |
| FastAPI (uvicorn) | ~100 |
| XGBoost 모델 | ~50 |
| Prophet 모델 | ~100 |
| Python 런타임 | ~150 |
| nginx (frontend) | ~20 |
| **합계** | **~920** |
| **여유** | **~1080** |

**LSTM 프리로딩 제거의 효과:** 기존 설계에서는 API 기동 시 LSTM 모델을 메모리에 프리로딩하고 있었다. LSTM 모델은 PyTorch 런타임 포함 약 200MB를 점유하는데, API에서 LSTM 모델을 선택할 수 있는 엔드포인트가 존재하지 않았다. 따라서 프리로딩을 제거하여 **~200MB를 절약**하였으며, 여유 메모리가 ~880MB에서 ~1080MB로 확대되었다.

이 결정은 2GB 제약 환경에서 특히 중요하다. PostgreSQL과 FastAPI가 동시에 부하를 받을 경우 여유 메모리가 안전 버퍼 역할을 한다. docker-compose.yml에도 리소스 제한(api: 1024M, db: 512M)을 설정하여 컨테이너 간 메모리 경합을 방지하였다.

---

## 5. Portainer + Nginx Proxy Manager 구성

### 5.1 Portainer — Docker 스택 관리

Portainer는 Web UI 기반 Docker 관리 도구로, 다음 역할을 수행한다.

| 기능 | 설명 |
|------|------|
| 스택 배포 | docker-compose.yml을 Web UI에서 직접 배포/업데이트 |
| 환경변수 관리 | `.env` 파일 없이 Portainer UI에서 환경변수 설정 |
| 컨테이너 로그 | 실시간 로그 확인 및 필터링 |
| 재시작/재배포 | 개별 컨테이너 또는 전체 스택 재시작 |

### 5.2 Nginx Proxy Manager — 리버스 프록시

| 기능 | 설명 |
|------|------|
| 리버스 프록시 | 도메인/경로 기반으로 api, frontend 컨테이너에 트래픽 분배 |
| SSL 인증서 | Let's Encrypt 인증서 자동 발급 및 갱신 |
| 접근 제어 | IP 기반 접근 제한, Basic Auth 설정 |

### 5.3 배포 환경변수

```
POSTGRES_PASSWORD=********        # DB 비밀번호 (Portainer에서 설정)
CORS_ORIGINS=https://example.com  # 허용 오리진 (쉼표 구분)
MODEL_VERSION=v1                  # 모델 버전 (saved/ 하위 경로)
VITE_API_BASE_URL=https://api.example.com  # 프론트엔드 API 주소
```

모든 환경변수는 Portainer의 스택 환경변수 기능으로 관리하며, `.env` 파일을 서버에 직접 배치하지 않는다.

---

## 6. AI 활용 효과 분석

### 6.1 활용 방식별 효과

| 활용 방식 | 효과 |
|----------|------|
| 코드 전수 검사 (Architect) | 배포 전 20건 이슈 사전 발견 — 서버 장애 방지 |
| 심각도 분류 | CRITICAL/HIGH/MEDIUM 3단계로 우선순위화 — 효율적 수정 순서 확보 |
| 의존관계 분석 | Phase 내 수정 순서 자동 도출 (경로 먼저 → 나머지 병렬) |
| 메모리 예산 계산 | 2GB 제약에서 컴포넌트별 사용량 분석 — LSTM 프리로딩 제거 결정 |
| 보안 점검 | DB 크레덴셜 노출, `torch.load` 취약점, traceback 노출 등 보안 이슈 식별 |

### 6.2 로컬-서버 환경 차이 탐지

이번 진단에서 발견된 이슈의 대부분은 **로컬 환경에서는 드러나지 않는** 서버 특화 문제이다.

| 이슈 유형 | 로컬에서 드러나지 않는 이유 |
|----------|--------------------------|
| 상대 경로 | 로컬에서는 프로젝트 루트에서 실행하므로 경로 정상 동작 |
| CORS | 프론트/백엔드 모두 localhost이므로 차단되지 않음 |
| 메모리 | 16GB+ 환경에서는 LSTM 프리로딩도 문제없음 |
| `n_jobs=-1` | 멀티코어 환경에서는 오히려 성능 향상 |
| DB 크레덴셜 | 로컬 Docker Compose에서는 외부 노출 위험이 낮음 |

AI가 **서버 환경을 가정한 정적 분석**을 수행함으로써, 수동 배포 시 이슈당 빌드-배포-테스트 사이클(~10분)을 20회 반복하는 대신 20건을 일괄 도출하여 Phase별로 수정할 수 있었다.

---

## 7. 한계점

1. **Portainer/NPM 설정은 AI가 직접 수행 불가.** Portainer와 Nginx Proxy Manager는 Web UI를 통해 설정하므로, AI가 CLI로 조작할 수 없다. 스택 배포, SSL 인증서 설정, 프록시 규칙 생성은 모두 수동 작업으로 진행하였다.

2. **실제 트래픽 부하 테스트 미수행.** Uvicorn의 `limit-concurrency=10` 설정과 Docker 리소스 제한이 실제 부하에서 적정한지 검증하지 못하였다. 동시 10건 요청 수준의 간이 테스트만 수행하였으며, 실사용 트래픽 패턴에 대한 부하 테스트는 향후 과제이다.

3. **SSL 인증서 및 도메인 설정은 수동 작업.** Let's Encrypt 인증서 발급, DNS 레코드 설정, Nginx Proxy Manager의 프록시 호스트 구성 등은 AI 자동화 범위 밖이다.

4. **PostgreSQL은 현재 실질 미사용.** DB 컨테이너가 기동되어 health check를 통과하지만, 실제 데이터는 전부 CSV 파일 기반으로 처리된다. DB 마이그레이션(Alembic)과 ORM 쿼리가 실 데이터로 동작하는지는 검증되지 않았다. 향후 CSV에서 DB로 전환할 때 추가 이슈가 발생할 가능성이 있다.

---

## 8. 수정 파일 목록

### Phase 1: CRITICAL (8개 파일)

| 파일 | 변경 유형 |
|------|----------|
| `edupulse/constants.py` | 수정 — `PROJECT_ROOT` 기반 절대 경로 상수 추가 |
| `edupulse/api/middleware.py` | 수정 — CORS origins 환경변수화 |
| `edupulse/api/main.py` | 추가 — 글로벌 예외 핸들러 |
| `edupulse/database.py` | 수정 — DB URL 환경변수화 |
| `docker-compose.yml` | 수정 — 크레덴셜 환경변수 치환 |
| `Dockerfile` | 수정 — Python 3.11 → 3.12, uvicorn 프로덕션 설정 |
| `scripts/deploy.sh` | 수정 — docker compose v2 문법, 마이그레이션 추가 |
| `.env.example` | 수정 — 신규 환경변수 템플릿 반영 |

### Phase 2: HIGH (7개 파일)

| 파일 | 변경 유형 |
|------|----------|
| `edupulse/model/xgboost_model.py` | 수정 — `n_jobs=1` |
| `edupulse/model/lstm_model.py` | 수정 — `weights_only=True` |
| `edupulse/model/predict.py` | 수정 — CSV 캐싱 통일, 동시 로딩 Lock |
| `edupulse/model/ensemble.py` | 수정 — confidence 역전 방지 |
| `edupulse/database.py` | 수정 — 커넥션 풀 제한 |
| `edupulse/api/main.py` | 수정 — 모델 프리로딩 로깅 |
| `.dockerignore` | 추가/수정 — frontend, tests, .env 제외 |

### Phase 3: MEDIUM (5개 파일)

| 파일 | 변경 유형 |
|------|----------|
| `edupulse/api/main.py` | 수정 — LSTM 프리로딩 제거 |
| `edupulse/model/predict.py` | 수정 — CSV 캐시 mtime 기반 갱신 |
| `requirements-server.txt` | 수정 — 서버 전용 패키지 독립화 |
| `docker-compose.yml` | 수정 — 리소스 제한 추가 (mem_limit) |
| `docker-compose.dev.yml` | 수정 — version 키 제거 |
