# 서버 배포 전 이슈 수정 계획

> 대상: Digital Ocean Droplet (1 vCPU / 2GB RAM, CPU only)
> 배포 방식: Portainer (Docker Compose 스택)
> 날짜: 2026-04-10

---

## Phase 1: CRITICAL — 배포 차단 이슈 (6건)

### 1.1 Dockerfile Python 3.12 업그레이드
- **파일**: `Dockerfile:1`
- **변경**: `FROM python:3.11-slim` → `FROM python:3.12-slim`
- **이유**: 로컬 학습환경(3.12)과 일치시켜 LSTM 모델 pickle 호환성 보장
- **검증**: `docker build` 성공 확인

### 1.2 상대 경로 → PROJECT_ROOT 기반 절대 경로
- **파일**: `edupulse/constants.py:17-25`, `edupulse/model/predict.py:41-45`, `edupulse/model/retrain.py:14-16`
- **변경**:
  - `constants.py`에 `PROJECT_ROOT = Path(__file__).resolve().parent.parent` 정의
  - 모든 데이터/모델 경로를 `PROJECT_ROOT / "edupulse/..."` 형태로 변경
  - `predict.py`의 `_MODEL_PATHS`, `_ENROLLMENT_PATH` 등 경로 상수 → `constants.py`에서 import
  - `retrain.py`의 `_MODEL_SAVE_DIRS` → `constants.py` 경로 사용
  - `config.py:20`의 `model_dir` → `PROJECT_ROOT` 기반으로 변경하거나 제거(미사용)
- **검증**: Docker 컨테이너 내 `WORKDIR /app`에서 모델 로딩 테스트

### 1.3 CORS 환경변수 기반으로 변경
- **파일**: `edupulse/api/middleware.py:10-13`
- **변경**:
  ```python
  import os
  origins = os.environ.get(
      "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
  ).split(",")
  ```
- **docker-compose.yml에 추가**: `CORS_ORIGINS: "http://<droplet-ip>:3000"` (또는 도메인)
- **검증**: 브라우저 콘솔에서 CORS 에러 없음 확인

### 1.4 DB 크레덴셜 환경변수화
- **파일**: `docker-compose.yml:6-8,21`, `alembic.ini:62`
- **변경**:
  - `docker-compose.yml`: `${POSTGRES_PASSWORD}` 등 환경변수 치환 사용
  - `alembic.ini:62`: placeholder URL로 교체 (runtime에서 `env.py`가 override)
  - `.env.example` 업데이트
- **Portainer 참고**: Portainer 스택 배포 시 Environment variables 섹션에서 설정
- **검증**: `docker compose config`로 변수 치환 확인

### 1.5 글로벌 예외 핸들러 추가
- **파일**: `edupulse/api/main.py`
- **변경**:
  ```python
  @app.exception_handler(Exception)
  async def global_exception_handler(request: Request, exc: Exception):
      logger.error("Unhandled: %s", exc, exc_info=True)
      return JSONResponse(status_code=500, content={"detail": "Internal server error"})
  ```
- **검증**: 의도적 에러 발생 시 traceback 노출 안 됨 확인

### 1.6 deploy.sh 마이그레이션 + docker compose v2
- **파일**: `scripts/deploy.sh:8-10`
- **변경**:
  - `docker-compose` → `docker compose` (v2 문법)
  - `docker compose up --build -d` 후 `docker compose exec api alembic upgrade head` 추가
  - 인자 검증 추가 (`$1` 없으면 usage 출력)
- **검증**: `deploy.sh` dry-run

---

## Phase 2: HIGH — 안정성/보안 (8건)

### 2.1 XGBoost n_jobs 제한
- **파일**: `edupulse/model/xgboost_model.py:49`
- **변경**: `"n_jobs": -1` → `"n_jobs": int(os.environ.get("XGBOOST_N_JOBS", 1))`
- **검증**: 서버에서 CPU 사용률 모니터링

### 2.2 torch.load() weights_only=True
- **파일**: `edupulse/model/lstm_model.py:698`
- **변경**: `torch.load(model_pt, map_location=device, weights_only=True)`
- **검증**: LSTM 모델 로딩 테스트

### 2.3 CSV 캐싱 통일
- **파일**: `edupulse/model/predict.py:301-369`
- **변경**: 5개 uncached `pd.read_csv()` → `load_csv_cached()` 사용
  - L303: consultation_logs.csv
  - L316: web_logs.csv
  - L330: cert_exam_schedule.csv
  - L345: competitor_courses.csv
  - L361: seasonal_factors.csv
- **검증**: API 호출 시 disk I/O 감소 확인 (두 번째 호출부터 캐시 적중)

### 2.4 DB 커넥션 풀 제한
- **파일**: `edupulse/database.py:12`
- **변경**:
  ```python
  engine = create_engine(
      settings.database_url,
      pool_pre_ping=True,
      pool_size=3,
      max_overflow=2,
      pool_recycle=1800,
  )
  ```
- **검증**: 동시 요청 테스트 시 connection 에러 없음

### 2.5 모델 프리로딩 로깅
- **파일**: `edupulse/api/dependencies.py:20-22`
- **변경**: `except Exception: pass` → `except Exception as e: logger.warning(...)`
- **추가**: LSTM 프리로딩 제거 (API에서 선택 불가 + 200MB RAM 절약)
- **검증**: 서버 시작 로그에서 모델 로딩 상태 확인

### 2.6 .dockerignore 보완
- **파일**: `.dockerignore`
- **추가**:
  ```
  .env
  .env.*
  edupulse/data/processed/
  edupulse/data/warehouse/
  frontend/
  tests/
  .claude/
  scripts/
  ```
- **검증**: `docker build` 후 이미지 크기 감소 확인

### 2.7 동시 모델 로딩 방어
- **파일**: `edupulse/model/predict.py:86-102`
- **변경**: per-model lock 추가하여 동일 모델 동시 로딩 방지
  ```python
  _loading_locks: dict[str, threading.Lock] = {}
  ```
- **검증**: 동시 요청 시 OOM 없음

### 2.8 Ensemble confidence 역전 방지
- **파일**: `edupulse/model/ensemble.py:166`
- **변경**: `confidence_upper = max(confidence_upper, confidence_lower)` 추가
- **검증**: edge case 입력으로 upper >= lower 확인

---

## Phase 3: MEDIUM — 개선사항 (6건)

### 3.1 LSTM 프리로딩 제거 (2.5와 연계)
- `dependencies.py:18`에서 `"lstm"` 제거 → RAM ~200MB 절약

### 3.2 CSV 캐시 mtime 기반 갱신
- `predict.py:load_csv_cached()`에 mtime 체크 추가 (모델 캐시와 동일 패턴)

### 3.3 requirements-server.txt 독립화
- `requirements.txt` 전체 import 대신 서버에 필요한 패키지만 명시
- pytest, beautifulsoup4, pytrends 등 제외

### 3.4 Uvicorn 프로덕션 설정
- `Dockerfile:8` CMD에 `--timeout-keep-alive 30 --limit-concurrency 10` 추가

### 3.5 docker-compose.yml 리소스 제한
- api: `deploy.resources.limits.memory: 1024M`
- db: `deploy.resources.limits.memory: 512M`
- **참고**: Portainer에서 리소스 제한 설정 가능

### 3.6 docker-compose.dev.yml version 키 제거
- `version: "3.9"` 제거 (Docker Compose v2에서 obsolete)

---

## 실행 순서

```
Phase 1 (CRITICAL) → 테스트 → Phase 2 (HIGH) → 테스트 → Phase 3 (MEDIUM)
```

Phase 1 내부 의존관계:
- 1.2 (경로) 먼저 → 1.5 (예외핸들러)와 1.3 (CORS) 병렬 → 1.4 (크레덴셜) → 1.1 (Dockerfile) → 1.6 (deploy.sh)

## Acceptance Criteria

- [ ] `docker build` Python 3.12 기반으로 성공
- [ ] Docker 컨테이너 내 모든 모델/데이터 경로 정상 resolve
- [ ] CORS: Droplet IP에서 프론트엔드 API 호출 성공
- [ ] DB 크레덴셜이 docker-compose.yml에 평문으로 없음
- [ ] 모델 에러 시 structured JSON 500 반환 (traceback 미노출)
- [ ] `alembic upgrade head` 배포 시 자동 실행
- [ ] `.venv/bin/python -m pytest tests/ -v` 전체 통과
- [ ] 서버 기동 로그에서 모델 로딩 상태 확인 가능
- [ ] 동시 10건 요청 시 OOM 없음
