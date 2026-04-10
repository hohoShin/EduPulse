# 🫀 EduPulse — AI 기반 수강 신청 수요 예측 솔루션

> **공모전 주제** : AI 활용 차세대 교육 솔루션  
> **주최** : 코딩·보안·게임·아트 학원  
> **핵심 방향** : AI 분석 및 예측 모델을 기반으로 교육 운영자의 실질적 페인포인트를 해결

---

## 🎯 프로젝트 개요

교육 현장에서 강좌 수요를 정확히 예측하지 못해 발생하는 **폐강, 강사 수급 실패, 마케팅 낭비** 문제를 AI 예측 모델로 해결합니다.  
수강 이력, 검색 트렌드, 채용 시장 데이터 등을 통합 분석하여 **기수별 수강 신청 수요를 사전에 예측**하고, 이를 운영·마케팅·전략 의사결정에 자동으로 연결합니다.

---

## 💡 핵심 서비스 기능

### 🏢 운영 효율화
| 기능 | 설명 |
|---|---|
| 강사 수급 자동 스케줄링 | 예측 수요 기반 강사 배정 및 강의실 편성 자동 제안 |
| 최적 개강 시점 추천 | 수요 예측 + 경쟁 학원 일정 + 취업 시장 사이클 결합 |
| 폐강 리스크 예측 | 수강 미달 위험 강좌 사전 감지 및 대응 알림 |

### 💰 마케팅·매출 연계
| 기능 | 설명 |
|---|---|
| 동적 수강료 최적화 | 수요 예측 기반 얼리버드 기간 및 할인율 자동 조정 |
| 광고 타이밍 예측 | 수강 신청 피크 2~3주 전 광고 집행 타이밍 자동 추천 |
| 잠재 수강생 전환 예측 | 상담 후 미등록자 전환 가능성 예측 및 리타겟팅 우선순위 정렬 |

### 🗺️ 전략 기획
| 기능 | 설명 |
|---|---|
| 신규 강좌 개설 시뮬레이터 | 강좌 신설 시 예상 수요 시뮬레이션 |
| 연령·목적별 수요 세분화 | 연령대(20대/30대/40대+) 및 수강 목적(취업/취미/자격증)별 수요 패턴 분석 |
| 경쟁 학원 동향 연동 | 경쟁사 개강·커리큘럼 변화를 예측 모델에 자동 반영 |

---

## 합성 데이터 안내

> 본 프로젝트는 현재 **합성(Synthetic) 데이터**로 개발 및 검증을 진행하고 있습니다.
> 실제 학원 운영 데이터를 확보할 수 없는 상황이므로, 현실적인 패턴(계절성, 코로나 충격, 성장 트렌드)을 시뮬레이션한 합성 데이터를 사용합니다.

- **용도:** 모델 아키텍처, 전처리 파이프라인, API 통합의 정상 동작 검증
- **한계:** MAPE 수치는 시스템 검증 목적이며, 실전 예측 성능과 다를 수 있음
- **전환:** 실제 데이터 확보 시 CSV 파일 교체만으로 전환 가능 (파이프라인 재사용)
- **상세 문서:** [`docs/합성_데이터_생성_가이드.md`](docs/합성_데이터_생성_가이드.md)

---

## 🗂️ 데이터 파이프라인

```
[01 수집] → [02 전처리] → [03 모델링] → [04 서비스]
```

### 01. 데이터 수집

**내부 데이터 (학원 자체 보유)**
- 수강 이력 DB : 기수별 등록 인원, 조기 마감/폐강 이력
- 상담 로그 : 문의 건수, 상담 후 미등록 사유, 전환율
- 학생 프로필 : 연령대, 직업군, 수강 목적
- 웹/앱 로그 : 페이지뷰, 장바구니 이탈, 광고 클릭률

**외부 데이터 (공개 수집)**
- 네이버 데이터랩 / Google Trends : 키워드 검색량 트렌드
- 채용 공고 크롤링 : 직군별 공고 수 변화 (코딩·보안·게임·아트)
- 자격증 시험 일정 : 정보처리기사, 정보보안기사 등
- 경쟁 학원 모니터링 : 개강 일정·수강료 크롤링
- 계절·시기 데이터 : 방학, 수능, 학기 시작 등 사이클

### 02. 데이터 전처리

- **정제** : 결측치 보간, IQR/Z-score 기반 이상치 탐지
- **변환** : 월별 집계, 슬라이딩 윈도우, 시계열 정렬
- **피처 엔지니어링** : 시즌 변수, 지연 변수(lag), 이동 평균 생성
- **통합** : 내부 + 외부 멀티소스 데이터 병합
- **적재** : 정형화된 학습용 데이터셋 → 데이터 웨어하우스

### 03. AI 모델링

| 항목 | 내용 |
|---|---|
| 예측 모델 후보 | Prophet, LSTM, XGBoost |
| 출력 형태 | 강좌별 수요 등급 (High / Mid / Low) + 예상 등록 인원 |
| 검증 방식 | 시계열 K-Fold 교차 검증, MAPE 기준 평가 |
| 재학습 주기 | 매 기수 종료 후 신규 데이터 추가 학습 (자동화) |

### 04. 서비스 출력

- 운영 대시보드 : 예측 수요 시각화, 강사 배정 제안, 개강 추천
- 마케팅 알림 : 광고 타이밍·수강료 조정 자동 알림
- 전략 리포트 : 신규 강좌 시뮬레이션, 경쟁 분석 결과

---

## 📊 데이터 수집 난이도

| 데이터 | 중요도 | 수집 난이도 |
|---|---|---|
| 수강 이력 | ★★★★★ | 낮음 (자체 보유) |
| 상담 데이터 | ★★★★ | 낮음 (자체 보유) |
| 검색 트렌드 | ★★★★ | 낮음 (무료 API) |
| 채용 공고량 | ★★★★ | 중간 (크롤링) |
| 계절·시기 | ★★★ | 낮음 (공개 데이터) |
| 경쟁 학원 동향 | ★★★ | 중간 (크롤링) |
| 웹 로그 | ★★★ | 낮음 (GA 연동) |
| 자격증 일정 | ★★ | 낮음 (공개 데이터) |

---

## 🛠️ 기술 스택

| 영역 | 기술 |
|---|---|
| 데이터 수집 | Python (BeautifulSoup, Selenium), Naver API, Google Trends API |
| 전처리 | Pandas, NumPy, scikit-learn |
| 모델링 | Prophet, PyTorch (LSTM), XGBoost |
| 서빙 | FastAPI, Docker |
| 시각화 | React, Recharts, Plotly |
| 데이터 저장 | PostgreSQL |

## 🖥️ 실행 환경

| | M4 맥북 (로컬) | Digital Ocean Droplet |
|---|---|---|
| **용도** | 개발, 실험, LSTM 학습 | XGBoost·Prophet 자동 재학습, API 서빙 |
| **사양** | M4 / MPS 가속 | 1 vCPU / 2GB RAM |
| **LSTM 재학습** | ✅ 수동 학습 후 S3 업로드 | ❌ 사양 부족으로 제외 |

Droplet 사양 한계로 LSTM은 서버 자동 재학습에서 제외합니다.
맥북에서 수동 학습 후 scp로 모델 파일을 서버에 직접 전송하면 서버가 이를 불러와 서빙합니다.

```bash
scp model/saved/lstm/model.pt user@your-droplet-ip:/app/model/saved/lstm/
```

## 🖥️ 프론트엔드 (Phase A)

현재 프론트엔드는 **Phase A: Mock-First Scaffold** 단계에 있습니다. 백엔드 서버 없이도 핵심 기능을 시뮬레이션하고 UI를 확인할 수 있습니다.

### 주요 기능
- **Dashboard**: 분야별 수요 예측 트렌드 시각화 (Curated Demo)
- **Simulator**: 신규 강좌 정보 입력 시 수요 등급 및 대응 전략 시뮬레이션
- **Adapter Pattern**: Mock 데이터와 실데이터를 유연하게 전환할 수 있는 구조

### 로컬 실행 방법
```bash
cd frontend
npm install
npm run dev
```
- 접속 주소: `http://localhost:5173/`

### 상세 개발 단계
- 현재 상태: Phase A 완료 (Mock 기반)
- 다음 단계: Phase B (Contract Hardening)
- 상세 로드맵: [`docs/ai_plans/edupulse-frontend-phases.md`](docs/ai_plans/edupulse-frontend-phases.md)

---

## 📁 프로젝트 파일 구조

```
edupulse/                              # 프로젝트 루트
│
├── edupulse/                          # 메인 Python 패키지
│   ├── config.py                      # 환경 설정 (DB, API 키 등)
│   ├── constants.py                   # 상수 정의 (분야, 키워드 등)
│   ├── database.py                    # DB 연결 및 세션 관리
│   │
│   ├── api/                           # 백엔드 API 서버
│   │   ├── main.py                    # FastAPI 앱 엔트리포인트
│   │   ├── dependencies.py            # 의존성 주입
│   │   ├── middleware.py              # 미들웨어 (CORS 등)
│   │   ├── routers/
│   │   │   ├── demand.py              # 수요 예측 엔드포인트
│   │   │   ├── schedule.py            # 강사 스케줄링 엔드포인트
│   │   │   ├── marketing.py           # 마케팅 타이밍 엔드포인트
│   │   │   └── health.py             # 헬스체크 엔드포인트
│   │   └── schemas/                   # Pydantic 요청/응답 스키마
│   │       ├── common.py              # 공통 스키마
│   │       ├── demand.py
│   │       ├── marketing.py
│   │       └── schedule.py
│   │
│   ├── collection/                    # 데이터 수집
│   │   └── api/                       # 외부 API 연동
│   │       ├── collect_search_trends.py  # 수집 오케스트레이터 (CLI 진입점)
│   │       ├── naver_datalab.py       # 네이버 데이터랩 검색 트렌드
│   │       ├── google_trends.py       # Google Trends (캐시 전용)
│   │       ├── keywords.py            # 분야별 키워드 매핑
│   │       └── quota.py              # Naver API 일일 쿼터 관리
│   │
│   ├── data/                          # 데이터 저장소 및 생성기
│   │   ├── generators/                # 합성 데이터 생성기
│   │   │   ├── enrollment_generator.py  # 수강 이력 합성
│   │   │   ├── external_generator.py    # 외부 데이터 합성
│   │   │   └── run_all.py             # 전체 합성 데이터 생성 실행
│   │   ├── raw/                       # 수집 원본 데이터
│   │   │   ├── internal/              # 내부 데이터 (수강 이력, 상담 로그 등)
│   │   │   └── external/              # 외부 데이터 (검색 트렌드, 채용 공고 등)
│   │   ├── processed/                 # 전처리 완료 데이터
│   │   └── warehouse/                 # 학습용 최종 데이터셋
│   │
│   ├── db_models/                     # SQLAlchemy DB 모델
│   │   ├── course.py                  # 강좌 모델
│   │   ├── enrollment.py              # 수강 등록 모델
│   │   └── prediction.py              # 예측 결과 모델
│   │
│   ├── model/                         # AI 모델링
│   │   ├── base.py                    # 모델 베이스 클래스
│   │   ├── train.py                   # 모델 학습
│   │   ├── predict.py                 # 수요 예측 실행
│   │   ├── evaluate.py                # 성능 평가 (MAPE, K-Fold)
│   │   ├── retrain.py                 # 자동 재학습 스케줄러
│   │   ├── ensemble.py                # 앙상블 모델
│   │   ├── prophet_model.py           # Prophet 모델
│   │   ├── lstm_model.py              # LSTM 모델
│   │   ├── xgboost_model.py           # XGBoost 모델
│   │   ├── utils.py                   # 모델 유틸리티
│   │   └── saved/                     # 학습된 모델 저장
│   │       ├── prophet/
│   │       ├── lstm/
│   │       └── xgboost/
│   │
│   └── preprocessing/                 # 데이터 전처리
│       ├── cleaner.py                 # 결측치·이상치 처리
│       ├── transformer.py             # 시계열 변환, 피처 엔지니어링
│       └── merger.py                  # 멀티소스 데이터 병합
│
├── alembic/                           # DB 마이그레이션
│   └── versions/
│       └── 001_initial.py             # 초기 테이블 생성
│
├── scripts/                           # 실행 스크립트
│   └── run_pipeline.py                # 전체 파이프라인 실행
│
├── tests/                             # 테스트
│   ├── conftest.py                    # 테스트 픽스처
│   ├── test_collection.py             # 데이터 수집 테스트
│   ├── test_preprocessing.py          # 전처리 테스트
│   ├── test_model.py                  # 모델 테스트
│   ├── test_demand.py                 # 수요 예측 API 테스트
│   └── test_health.py                # 헬스체크 테스트
│
├── frontend/                      # 대시보드 프론트엔드 (Phase A)
│   ├── src/
│   │   ├── api/
│   │   │   ├── adapters/          # Mock/Real 데이터 어댑터
│   │   │   ├── viewModels.js      # UI용 데이터 변환 로직
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx      # 메인 예측 대시보드 (Demo)
│   │   │   └── Simulator.jsx      # 수요 시뮬레이터 (Mock-First)
│   │   └── components/
│   │       ├── DemandChart.jsx    # 수요 예측 시각화
│   │       ├── AlertPanel.jsx     # 폐강 리스크·광고 알림
│   │       └── StatusPanel.jsx    # 시스템 상태 표시
│   └── README.md
```

---

## 🧪 데이터 생성 및 모델 테스트 가이드

### 사전 준비

```bash
# 1. 가상환경 활성화
# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# 2. 개발용 패키지 설치 (jupyter, matplotlib, prophet, torch 포함)
pip install -r requirements-dev.txt
```

### 데이터 생성 및 파이프라인

```bash
# 합성 데이터 생성 → 전처리 → XGBoost 학습 (한 번에 실행)
python -m scripts.run_pipeline

# 기존 raw 데이터 유지하고 전처리 + 학습만 재실행
python -m scripts.run_pipeline --skip-generate

# 특정 모델만 학습
python -m scripts.run_pipeline --model prophet --version 1
python -m scripts.run_pipeline --model lstm --version 1
python -m scripts.run_pipeline --model all --version 1
```

**파이프라인 단계별 개별 실행:**

```bash
# 1단계: 합성 데이터 생성
python -m edupulse.data.generators.run_all

# 2단계: 개별 모델 학습
python -m edupulse.model.train --model xgboost --version 1
python -m edupulse.model.train --model prophet --version 1
python -m edupulse.model.train --model lstm --version 1
python -m edupulse.model.train --model all --version 1

# 3단계: 모델 성능 평가 (MAPE, 시계열 K-Fold)
python -m edupulse.model.evaluate --model xgboost
python -m edupulse.model.evaluate --model all        # 전체 비교표 출력
```

### Jupyter 노트북 실험 환경

```bash
# Jupyter 실행
jupyter notebook notebooks/
```

| 노트북 | 용도 |
|---|---|
| `eda.ipynb` | 데이터 분포, 시계열 트렌드, 계절성, 상관관계 탐색 |
| `feature_engineering.ipynb` | 피처 중요도 분석, 피처 조합별 MAPE 비교, 새 피처 실험 |
| `model_comparison.ipynb` | XGBoost / Prophet / LSTM / Ensemble MAPE 비교 + 시각화 |
| `model_experiments.ipynb` | 모델별 하이퍼파라미터 튜닝 (n_estimators, learning_rate 등) |
| `pipeline_test.ipynb` | 데이터 생성 → 전처리 → 학습 → 예측 end-to-end 검증 |

> 노트북은 Prophet/PyTorch 미설치 환경에서도 해당 모델을 건너뛰고 실행됩니다.
> 데이터가 없으면 노트북 내에서 자동 생성합니다.

### 단위 테스트

```bash
# 전체 테스트
pytest tests/

# 모델 테스트만 실행
pytest tests/test_model.py -v

# 특정 테스트
pytest tests/test_preprocessing.py -v
pytest tests/test_demand.py -v
```

### 생성되는 데이터 경로

| 단계 | 경로 | 내용 | 상태 |
|---|---|---|---|
| 합성 데이터 | `edupulse/data/raw/internal/enrollment_history.csv` | 수강 이력 | 합성 생성기 구현 완료 |
| 합성 데이터 | `edupulse/data/raw/internal/consultation_logs.csv` | 상담 로그 | 합성 생성기 구현 완료 |
| 합성 데이터 | `edupulse/data/raw/internal/student_profiles.csv` | 학생 프로필 | 합성 생성기 구현 완료 |
| 합성 데이터 | `edupulse/data/raw/internal/web_logs.csv` | 웹/앱 로그 | 합성 생성기 구현 완료 |
| 합성 데이터 | `edupulse/data/raw/external/search_trends.csv` | 검색 트렌드 | 합성 생성기 구현 완료 |
| 합성 데이터 | `edupulse/data/raw/external/job_postings.csv` | 채용 공고 | 합성 생성기 구현 완료 |
| 합성 데이터 | `edupulse/data/raw/external/cert_exam_schedule.csv` | 자격증 시험 일정 | 합성 생성기 구현 완료 |
| 합성 데이터 | `edupulse/data/raw/external/competitor_data.csv` | 경쟁 학원 데이터 | 합성 생성기 구현 완료 |
| 합성 데이터 | `edupulse/data/raw/external/seasonal_events.csv` | 계절성 이벤트 | 합성 생성기 구현 완료 |
| 전처리 | `edupulse/data/warehouse/training_dataset.csv` | 학습용 최종 데이터셋 | |
| 모델 저장 | `edupulse/model/saved/{모델명}/v{버전}/` | 학습된 모델 파일 | |

---

## 📌 기획 포인트 요약

> 본 솔루션은 단순 수요 예측에 그치지 않고,  
> **예측 결과를 운영·마케팅·전략 세 방향으로 자동 연결**하여  
> 교육 운영자의 실질적인 의사결정을 데이터 기반으로 전환합니다.