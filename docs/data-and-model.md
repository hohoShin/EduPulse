# EduPulse 데이터 & 모델 가이드

> **최종 업데이트:** 2026-04-10
> **현재 상태:** Phase D 완료

---

## 1. 전체 파이프라인 개요

```
[1. 데이터 생성 (9종)]     [2. 전처리]           [3. 모델 학습]        [4. API 서빙]

enrollment_generator        cleaner               XGBoost ──┐
  ↓ enrollment.csv           ↓ 결측치 보간          Prophet ──┼─ Ensemble → FastAPI
external_generator          merger                LSTM ─────┘
  ↓ search_trends.csv        ↓ [field,date] 병합                  /api/v1/demand (2)
  ↓ job_postings.csv        transformer                           /api/v1/schedule (1)
internal_generator           ↓ lag/rolling/인코딩                  /api/v1/marketing (2)
  ↓ consultation_logs.csv                                         /api/v1/simulation (4)
  ↓ student_profiles.csv   training_dataset.csv                   /api/v1/health (1)
  ↓ web_logs.csv             (1668행 × 19피처)
schedule_generator
  ↓ cert_exam_schedule.csv
  ↓ competitor_data.csv
  ↓ seasonal_events.csv
```

**실행 커맨드:**
```bash
# 전체 파이프라인
.venv/bin/python scripts/run_pipeline.py

# 개별 단계
.venv/bin/python -m edupulse.data.generators.run_all     # 데이터 생성
.venv/bin/python -m edupulse.model.train --model all     # 학습
.venv/bin/python -m edupulse.model.evaluate --model all  # 평가
```

> **중요:** 반드시 `.venv/bin/python` (Python 3.12) 사용. 시스템 python3 (3.11)은 torch MPS segfault 발생.

API 엔드포인트 상세 --> architecture.md SS6 참조

---

## 2. 합성 데이터 설계

### 2.1 왜 합성 데이터인가

EduPulse는 학원의 수강 신청 수요를 예측하는 솔루션이다. 그러나 **실제 학원 운영 데이터를 확보할 수 없는** 상황이므로, 현실적인 패턴을 시뮬레이션한 합성 데이터로 모델 개발과 검증을 진행한다.

**합성 데이터의 역할:**

| 역할 | 설명 |
|------|------|
| 모델 아키텍처 검증 | XGBoost, Prophet, LSTM 파이프라인이 정상 동작하는지 확인 |
| 전처리 로직 검증 | lag feature, 순환 인코딩, 병합 등의 정확성 검증 |
| 평가 체계 검증 | TimeSeriesSplit K-Fold, MAPE 계산 로직 검증 |
| API 통합 테스트 | FastAPI 엔드포인트의 입출력 형식 검증 |

**합성 데이터의 한계:**

- 생성기가 심어놓은 패턴을 모델이 재발견하는 **자기순환 구조**
- 실제 데이터의 불규칙성, 결측 패턴, 외부 충격을 완전히 재현할 수 없음
- MAPE 수치는 시스템 검증 목적이며, 실제 예측 성능의 지표로 해석하면 안 됨
- 실 서비스 투입 전 반드시 **실제 학원 데이터로 재학습 및 재평가** 필요

### 2.2 데이터 생성 구조

```
run_all.py (오케스트레이터)
  │
  ├── 1. enrollment_generator.py
  │      └── enrollment_history.csv (수강 이력) ← 전체 원천 데이터
  │
  ├── 2. external_generator.py → generate_search_trends()
  │      └── search_trends.csv (검색 트렌드)
  │
  ├── 3. external_generator.py → generate_job_postings()
  │      └── job_postings.csv (채용 공고)
  │
  ├── 4. internal_generator.py → generate_consultation_logs()
  │      └── consultation_logs.csv (상담 로그)
  │
  ├── 5. internal_generator.py → generate_student_profiles()
  │      └── student_profiles.csv (학생 프로필)
  │
  ├── 6. internal_generator.py → generate_web_logs()
  │      └── web_logs.csv (웹/앱 로그)
  │
  ├── 7. events_generator.py → generate_cert_exam_schedule()
  │      └── cert_exam_schedule.csv (자격증 시험 일정) [결정론적]
  │
  ├── 8. events_generator.py → generate_competitor_data()
  │      └── competitor_data.csv (경쟁 학원 데이터)
  │
  └── 9. events_generator.py → generate_seasonal_events()
         └── seasonal_events.csv (계절성 이벤트) [결정론적, field 없음]
```

검색 트렌드, 채용 공고, 상담 로그, 학생 프로필, 웹 로그, 경쟁 학원 데이터는 수강 이력을 **원천 데이터로** 참조하여 파생 생성된다. 자격증 일정과 계절성 이벤트는 캘린더 기반 결정론적 생성이다.

**출력 파일:**

| 파일 | 경로 | 행수 | 비고 |
|------|------|------|------|
| 수강 이력 | `data/raw/internal/enrollment_history.csv` | 1668행 | 원천 데이터 |
| 상담 로그 | `data/raw/internal/consultation_logs.csv` | 1668행 | enrollment 파생 |
| 학생 프로필 | `data/raw/internal/student_profiles.csv` | 1668행 | enrollment 파생 |
| 웹/앱 로그 | `data/raw/internal/web_logs.csv` | 1668행 | enrollment 파생 |
| 검색 트렌드 | `data/raw/external/search_trends.csv` | 1668행 | enrollment 파생 |
| 채용 공고 | `data/raw/external/job_postings.csv` | 1668행 | enrollment 파생 |
| 자격증 시험 일정 | `data/raw/external/cert_exam_schedule.csv` | 1668행 | 캘린더 기반 결정론적 |
| 경쟁 학원 데이터 | `data/raw/external/competitor_data.csv` | 1668행 | enrollment 파생 |
| 계절성 이벤트 | `data/raw/external/seasonal_events.csv` | 417행 | 캘린더 기반, field 없음 |

### 2.3 데이터 간 관계도

```
                         enrollment_generator.py
                                  │
                          enrollment_history.csv
                            (원천 데이터)
           ┌──────────┬──────────┼──────────┬──────────┐
           │          │          │          │          │
      선행 2~4주  선행 1~2주  선행 1~3주   동행      동행
           │          │          │          │          │
   search_trends  consultation  web_logs  job_postings  competitor_data
    (검색 트렌드)   (상담 로그)  (웹 로그)   (채용 공고)   (경쟁 학원)
           │          │          │          │          │
           └──────────┴──────────┼──────────┴──────────┘
                                 │
                   student_profiles   (enrollment 파생 — Dirichlet 분포)
                                 │
           ┌─────────────────────┤
           │                     │
   cert_exam_schedule     seasonal_events
    (자격증 시험 일정)      (계절성 이벤트)
    [결정론적, field별]    [결정론적, field 없음]
           │                     │
           └──────────┬──────────┘
                      │
                 merger.py
              [field, date] 기준
                LEFT JOIN
                      │
                 cleaner.py
              결측치 보간 + IQR 클리핑
                      │
               transformer.py
           lag, 순환 인코딩, 파생 피처
                      │
             training_dataset.csv
               (모델 학습용, 34컬럼)
```

---

## 3. 데이터 소스 상세 (9종 CSV)

### 3.1 수강 이력 (`enrollment_generator.py`)

**기본 규격:**

| 항목 | 값 |
|------|-----|
| 해상도 | 주간 (매주 월요일, `freq="W-MON"`) |
| 기간 | 2018-01-04 ~ 2025-12-29 (8년, 417주) |
| 분야 | coding, security, game, art (4개) |
| 총 행수 | 1668행 (4분야 x 417주) |

**생성 공식:**

```
enrollment_count = round(max(0, base × trend + seasonal + noise))
```

각 요소가 현실의 어떤 현상을 시뮬레이션하는지 아래에 설명한다.

**base — 분야별 주간 기본 수요:**

| 분야 | base | 설정 근거 |
|------|------|-----------|
| coding | 4명/주 | 가장 대중적인 IT 교육 분야 |
| security | 3명/주 | 자격증(정보보안기사) 수요 |
| game | 3명/주 | 게임 산업 성장에 따른 교육 수요 |
| art | 2명/주 | 상대적으로 니치한 분야 |

이 값들은 소규모 학원(분야당 주 2~8명 수준)을 가정한 것이다.

**trend — 연도별 거시 트렌드:**

`_compute_trend(year)` 함수가 연도별 승수를 계산한다:

```
승수
1.25 ┤
     │                                          ╭──── 2025: 1.23
1.20 ┤                                     ╭────╯
     │                                ╭────╯
1.15 ┤                           ╭────╯
     │                      ╭────╯ 연 5% 정상 성장
1.10 ┤                 ╭────╯
     │            ╭────╯ 연 10% 급증 (온라인 교육 붐)
1.05 ┤       ╭────╯
     │  ╭────╯ 연 3% 성장
1.00 ┤──╯ 2018
     │
0.95 ┤
     │
0.90 ┤       ╰── 2020: 0.88 (코로나 -15% 충격)
0.85 ┤
```

| 기간 | 트렌드 | 현실 근거 |
|------|--------|-----------|
| 2018~2019 | 연 3% 복리 성장 | IT 교육 시장 안정적 성장기 |
| 2020 | -15% 급감 | 코로나19 초기 충격으로 대면 교육 위축 |
| 2021~2022 | 연 10% 급증 | 비대면 전환 후 온라인 교육 붐 |
| 2023~2025 | 연 5% 성장 | 시장 정상화, 꾸준한 성장세 |

**구현:**

```python
def _compute_trend(year: int) -> float:
    if year <= 2019:
        return 1.0 * (1.03 ** (year - 2018))       # 안정 성장
    elif year == 2020:
        base_2019 = 1.0 * (1.03 ** 1)              # ~1.03
        return base_2019 * 0.85                      # COVID 충격
    elif year <= 2022:
        base_2020 = 1.0 * (1.03 ** 1) * 0.85       # ~0.876
        return base_2020 * (1.10 ** (year - 2020))  # 급성장 회복
    else:
        base_2022 = 1.0 * (1.03 ** 1) * 0.85 * (1.10 ** 2)  # ~1.059
        return base_2022 * (1.05 ** (year - 2022))  # 정상 성장
```

**seasonal — 월별 계절성:**

학원 교육의 현실적인 계절 패턴을 반영한다:

| 월 | 보정값 | 현실 근거 |
|----|--------|-----------|
| 1월 | +1.5 | 겨울 방학 -- 시간 여유로 수강 증가 |
| 2월 | +0.8 | 방학 말 -- 수강 감소 추세 |
| 3월 | -1.2 | 학기 시작 -- 학업/취업 준비로 수강 최저 |
| 4월 | -1.0 | 학기 중 |
| 5월 | -0.8 | 학기 중 |
| 6월 | 0.0 | 중립 (학기 말~방학 전환기) |
| 7월 | +2.0 | 여름 방학 -- 연간 수강 피크 |
| 8월 | +1.8 | 여름 방학 |
| 9월 | -1.0 | 2학기 시작 |
| 10월 | -1.0 | 학기 중 |
| 11월 | -0.8 | 학기 중 |
| 12월 | +0.5 | 연말 -- 소폭 증가 |

이 보정값은 base에 **가산**된다. 예를 들어 coding(base=4)의 7월:
- `4 x trend + 2.0 + noise` -- 트렌드 1.0 기준 약 6명

**noise — 랜덤 노이즈:**

```python
noise = rng.normal(0, 0.6)  # 평균 0, 표준편차 0.6
```

- 현실에서 매주 정확히 같은 수의 수강생이 등록하지 않으므로 변동을 시뮬레이션
- 표준편차 0.6은 base(2~4) 대비 15~30% 수준의 변동
- 너무 크면 모델이 패턴을 학습하기 어렵고, 너무 작으면 비현실적

**cohort — 기수 파생:**

```python
cohort = week_index // 8 + 1
```

- 8주(약 2개월)를 하나의 기수로 묶음
- 학원에서 보통 8~12주 단위로 기수를 운영하는 관행 반영
- 수강 이력의 부가 정보로만 사용, 모델 피처에는 포함하지 않음

**구체적 생성 예시:**

```
coding, 2020년 7월 첫째 주:
  base=4, trend=0.876, seasonal=+2.0, noise=+0.3
  → round(max(0, 4 × 0.876 + 2.0 + 0.3))
  → round(5.80) = 6명

art, 2023년 3월 첫째 주:
  base=2, trend=1.059, seasonal=-1.2, noise=-0.2
  → round(max(0, 2 × 1.059 + (-1.2) + (-0.2)))
  → round(0.72) = 1명

security, 2018년 1월 첫째 주:
  base=3, trend=1.0, seasonal=+1.5, noise=+0.1
  → round(max(0, 3 × 1.0 + 1.5 + 0.1))
  → round(4.6) = 5명
```

### 3.2 검색 트렌드 (`external_generator.py`)

**설계 의도:** "수강 등록이 늘기 **2~4주 전에** 관련 검색이 먼저 증가한다"는 **선행 지표** 관계를 시뮬레이션한다.

현실 근거: 잠재 수강생이 학원을 등록하기 전에 "코딩 교육", "보안 자격증 학원" 등을 먼저 검색하므로, 검색량은 등록의 선행 지표가 된다.

**생성 공식:**

```python
future_idx = min(i + rng.integers(2, 5), len(enrollments) - 1)  # 2~4주 후
future_enrollment = enrollments[future_idx]
search_volume = round(max(1, future_enrollment × correlation + noise))
```

**분야별 상관 계수:**

| 분야 | 계수 | 의미 |
|------|------|------|
| coding | 1.8 | 등록 1명당 검색량 ~1.8 |
| game | 1.6 | 게임 분야도 검색 활발 |
| security | 1.5 | 자격증 관련 검색 |
| art | 1.2 | 상대적으로 검색량 적음 |

**예시:**

```
coding, 2023년 3월 첫째 주:
  3주 후 enrollment = 5명
  search_volume = round(max(1, 5 × 1.8 + noise))
                = round(9.0 + 0.7) = 10
```

### 3.3 채용 공고 (`external_generator.py`)

**설계 의도:** "IT 채용 시장이 활발하면 관련 교육 수요도 높다"는 **동행 지표** 관계를 시뮬레이션한다.

현실 근거: 채용 공고가 많으면 취업 준비를 위한 교육 수요가 함께 증가하는 경향이 있다.

**생성 공식:**

```python
job_count = round(max(0, enrollment × correlation + noise))
```

검색 트렌드와 달리 **같은 시점의** enrollment을 참조한다 (동행 관계).

**분야별 상관 계수:**

| 분야 | 계수 | 의미 |
|------|------|------|
| security | 3.0 | 보안 인력 수요 높음 -- 교육 연관 최대 |
| coding | 2.5 | 개발자 채용 -- 교육 연관 높음 |
| game | 1.8 | 게임 산업 채용 |
| art | 1.0 | 예술 분야는 채용과 교육의 연관 낮음 |

**예시:**

```
security, enrollment=3:
  job_count = round(max(0, 3 × 3.0 + noise))
            = round(9.0 + 1.2) = 10

art, enrollment=2:
  job_count = round(max(0, 2 × 1.0 + noise))
            = round(2.0 - 0.5) = 2
```

### 3.4 상담 로그 (`internal_generator.py`)

**설계 의도:** "수강 등록이 늘기 **1~2주 전에** 상담 문의가 먼저 증가한다"는 **선행 지표** 관계를 시뮬레이션한다. 전환율(conversion_rate)은 등록 수가 많을수록 소폭 상승하는 경향을 반영한다.

**스키마:**

| 컬럼 | 타입 | 설명 |
|------|------|------|
| date | datetime | 주간 날짜 (월요일) |
| field | str | 분야 (coding/security/game/art) |
| consultation_count | int | 해당 주 상담 건수 |
| conversion_rate | float | 상담→등록 전환율 (0.05~0.65) |

**생성 공식:**

```
consultation_count = max(0, future_enrollment × CONSULT_MULTIPLIER + noise)
conversion_rate = clip(0.15 + 0.05 × (enrollment / max_enrollment) + noise, 0.05, 0.65)
```

**상수:**

| 분야 | CONSULT_MULTIPLIER | 의미 |
|------|-------------------|------|
| coding | 3.0 | 등록 1명당 선행 상담 3건 |
| security | 2.5 | 자격증 관심자 상담 많음 |
| game | 2.0 | 상담 전환 낮음 |
| art | 1.5 | 니치 분야, 상담 적음 |

### 3.5 학생 프로필 (`internal_generator.py`)

**설계 의도:** 분야별 수강생 연령대 분포와 수강 목적 분포를 Dirichlet 분포로 시뮬레이션한다. 파생 피처 `age_group_diversity`는 transformer.py에서 Shannon 엔트로피로 계산된다.

**스키마:**

| 컬럼 | 타입 | 설명 |
|------|------|------|
| date | datetime | 주간 날짜 |
| field | str | 분야 |
| age_20s_ratio | float | 20대 비율 |
| age_30s_ratio | float | 30대 비율 |
| age_40plus_ratio | float | 40대+ 비율 |
| purpose_career | float | 취업 목적 비율 |
| purpose_hobby | float | 취미 목적 비율 |
| purpose_cert | float | 자격증 목적 비율 |

연령대 비율의 합 = 1.0, 수강 목적 비율의 합 = 1.0 (Dirichlet 분포 보장).

**상수:**

| 분야 | 연령 alpha (20대/30대/40대+) | 목적 alpha (취업/취미/자격증) |
|------|---------------------------|---------------------------|
| coding | [5, 3, 1] | [5, 2, 2] |
| security | [3, 4, 2] | [3, 1, 5] |
| game | [6, 2, 1] | [3, 4, 1] |
| art | [3, 3, 3] | [2, 5, 1] |

### 3.6 웹/앱 로그 (`internal_generator.py`)

**설계 의도:** "수강 등록 **1~3주 전에** 페이지뷰가 증가하고, 등록 직전에 장바구니 이탈률이 감소한다"는 관계를 시뮬레이션한다.

**스키마:**

| 컬럼 | 타입 | 설명 |
|------|------|------|
| date | datetime | 주간 날짜 |
| field | str | 분야 |
| page_views | int | 해당 주 페이지뷰 수 (>= 1) |

**생성 공식:**

```
page_views = max(1, future_enrollment × PV_MULTIPLIER + noise)
```

**상수:**

| 분야 | PV_MULTIPLIER | 의미 |
|------|---------------|------|
| game | 18.0 | 게임 분야는 탐색 행동 많음 |
| coding | 15.0 | 코딩 분야 활발한 온라인 탐색 |
| security | 12.0 | 보안 분야 신중한 탐색 |
| art | 10.0 | 예술 분야 낮은 온라인 탐색 |

### 3.7 자격증 시험 일정 (`events_generator.py`)

**설계 의도:** "자격증 시험 시즌이 다가올수록 관련 분야 교육 수요가 증가한다"는 관계를 시뮬레이션한다. 캘린더 기반으로 생성되므로 seed 무관하게 **결정론적** 출력을 보장한다.

**스키마:**

| 컬럼 | 타입 | 설명 |
|------|------|------|
| date | datetime | 주간 날짜 |
| field | str | 분야 |
| has_cert_exam | int | 시험 있는 달 여부 (0/1) |
| weeks_to_exam | int | 다음 시험까지 남은 주 (0~26) |

**분야별 시험 월:**

| 분야 | 시험 월 | 실제 근거 |
|------|--------|---------|
| coding | 3, 5, 8월 | 정보처리기사 시험 일정 |
| security | 3, 9월 | 정보보안기사 시험 일정 |
| game | 6월 | 게임 관련 자격 |
| art | 5, 11월 | 예술 분야 자격 |

**weeks_to_exam 계산:** `_weeks_to_next_exam(current_date, field)`: 현재 날짜 이후 가장 가까운 시험일(해당 월 15일)까지의 주 수를 계산하며, 최대 26주로 제한한다.

### 3.8 경쟁 학원 데이터 (`events_generator.py`)

**설계 의도:** "경쟁 학원이 많이 개강할수록 우리 학원 수요도 함께 증가한다(시장 확대 효과)"는 **동행 지표** 관계를 시뮬레이션한다. 수강료는 수요에 따라 소폭 변동한다.

**스키마:**

| 컬럼 | 타입 | 설명 |
|------|------|------|
| date | datetime | 주간 날짜 |
| field | str | 분야 |
| competitor_openings | int | 경쟁 학원 개강 수 (>= 0) |
| competitor_avg_price | int | 경쟁 학원 평균 수강료 (원, 만 원 단위 반올림) |

**생성 공식:**

```
competitor_openings = max(0, enrollment × COMP_RATIO + seasonal + noise)
competitor_avg_price = BASE_PRICE × (1 + 0.1 × norm_enrollment + noise)
```

**상수:**

| 분야 | COMP_RATIO | BASE_PRICE |
|------|-----------|-----------|
| coding | 1.2 | 500,000원 |
| security | 0.8 | 600,000원 |
| game | 0.6 | 450,000원 |
| art | 0.5 | 400,000원 |

### 3.9 계절성 이벤트 (`events_generator.py`)

**설계 의도:** 방학, 시험 시즌, 학기 시작 등 **분야 공통 계절 패턴**을 이진 플래그로 표현한다. `field` 컬럼이 없으며, merger.py에서 date 기준으로 전체 분야에 LEFT JOIN된다. 캘린더 기반으로 생성되므로 seed 무관하게 **결정론적** 출력을 보장한다.

**스키마:**

| 컬럼 | 타입 | 설명 |
|------|------|------|
| date | datetime | 주간 날짜 |
| is_vacation | int | 방학 여부 (1월, 2월, 7월, 8월) |
| is_exam_season | int | 시험 시즌 여부 (6월, 11월, 12월) |
| is_semester_start | int | 학기 시작 여부 (3월, 9월) |

**예시:**

```
2023-01-02 → is_vacation=1, is_exam_season=0, is_semester_start=0
2023-03-06 → is_vacation=0, is_exam_season=0, is_semester_start=1
2023-07-03 → is_vacation=1, is_exam_season=0, is_semester_start=0
2023-11-06 → is_vacation=0, is_exam_season=1, is_semester_start=0
```

### 3.10 재현성 보장

모든 생성기에 `seed` 파라미터가 있어 동일한 seed로 실행하면 **항상 동일한 데이터**를 생성한다.

```python
generate_enrollment_history(seed=42)       # 기본값 42
generate_search_trends(seed=42)            # 기본값 42
generate_job_postings(seed=43)             # 기본값 43
generate_consultation_logs(seed=44)        # 기본값 44
generate_student_profiles(seed=45)         # 기본값 45
generate_web_logs(seed=46)                 # 기본값 46
generate_cert_exam_schedule(seed=47)       # 결정론적 (seed 무관)
generate_competitor_data(seed=48)          # 기본값 48
generate_seasonal_events(seed=47)          # 결정론적 (seed 무관)
```

이는 다음을 보장한다:
- 동일 환경에서 실행할 때마다 같은 데이터 -- 테스트 재현성
- 모델 성능 비교 시 데이터 변동 제거 -- 공정한 비교
- seed를 변경하면 다른 변형의 데이터를 생성하여 모델 강건성 테스트 가능

---

## 4. 전처리 파이프라인

### 4.1 처리 순서

```
9개 CSV 소스
├── enrollment_history.csv (기준 테이블)
├── search_trends.csv
├── job_postings.csv
├── consultation_logs.csv
├── student_profiles.csv
├── web_logs.csv
├── cert_exam_schedule.csv
├── competitor_data.csv
└── seasonal_events.csv
            │
    ┌───────▼────────┐
    │   merger.py    │  [field, date] 기준 left join (9개 → 1개)
    │   주간 정렬     │  seasonal은 field 없음 → date만으로 join
    └───────┬────────┘
            │
    ┌───────▼────────┐
    │  cleaner.py    │  결측치: linear interpolation
    │                │  이상치: IQR 방식 clip
    └───────┬────────┘
            │
    ┌───────▼────────┐
    │ transformer.py │  lag feature + rolling mean
    │                │  순환 인코딩 + field 인코딩
    │                │  age_group_diversity (Shannon entropy)
    └───────┬────────┘
            │
    training_dataset.csv (1668행 × 34컬럼, 이 중 19개가 FEATURE_COLUMNS)
```

### 4.2 병합 (`merger.py`)

```python
# 병합 키
join_keys = ["field", "date"]

# 날짜를 주 시작일(월요일)로 정규화
merged["date"] = merged["date"].dt.to_period("W").dt.start_time
```

- enrollment(내부)을 기준으로 나머지 8개 소스를 `LEFT JOIN`
- seasonal_events는 `field` 컬럼이 없으므로 `date`만으로 조인
- 병합 후 결측치는 `forward fill`

**JOIN 상세:**

| JOIN 대상 | JOIN 키 | 추가 컬럼 |
|-----------|---------|----------|
| search_trends.csv | field, date | `search_volume` |
| job_postings.csv | field, date | `job_count` |
| consultation_logs.csv | field, date | `consultation_count`, `conversion_rate` |
| student_profiles.csv | field, date | `age_20s_ratio`, `age_30s_ratio`, `age_40plus_ratio`, `purpose_career`, `purpose_hobby`, `purpose_cert` |
| web_logs.csv | field, date | `page_views` |
| cert_exam_schedule.csv | field, date | `has_cert_exam`, `weeks_to_exam` |
| competitor_data.csv | field, date | `competitor_openings`, `competitor_avg_price` |
| seasonal_events.csv | **date만** | `is_vacation`, `is_exam_season`, `is_semester_start` |

후처리:
- 연속값 결측치: 분야별 forward fill (`groupby("field").ffill()`)
- 이진 플래그 결측치: 0으로 채움 (`has_cert_exam`, `is_vacation`, `is_exam_season`, `is_semester_start`)

### 4.3 정제 (`cleaner.py`)

**결측치 처리:**
```python
df[numeric_cols].interpolate(method="linear", limit_direction="both")
```
- 시계열 데이터이므로 `linear interpolation` 사용 (앞뒤 값의 평균)

**이상치 처리:**
```python
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR
df[col].clip(lower, upper)
```
- IQR(사분위범위) 방식으로 극단값을 경계값으로 대체
- 삭제가 아니라 **클리핑** -- 시계열의 연속성을 유지

### 4.4 피처 변환 (`transformer.py`)

**lag features (시차 특성):**
```python
# 분야별로 독립 shift — 분야 경계 오염 방지
df.groupby("field")["enrollment_count"].shift(lag)
```

| 피처 | 의미 |
|------|------|
| `lag_1w` | 1주 전 등록 인원 |
| `lag_2w` | 2주 전 등록 인원 |
| `lag_4w` | 4주 전 등록 인원 |
| `lag_8w` | 8주 전 등록 인원 |
| `rolling_mean_4w` | 최근 4주 이동평균 |

**순환 인코딩 (월 정보):**
```python
month_sin = sin(2π × month / 12)
month_cos = cos(2π × month / 12)
```
- 12월(12)과 1월(1)이 가까운 값이 되도록 삼각함수로 인코딩
- 단순 정수(1~12)로 하면 12→1 사이에 비연속적 점프가 생김

**분야 label encoding:**
```python
field_encoded = {"art": 0, "coding": 1, "game": 2, "security": 3}
```

**age_group_diversity (Shannon entropy):**
```python
# 연령대 비율의 정보 엔트로피 — 분포가 균등할수록 높은 값
entropy = -Σ(ratio × log(ratio))
```
- `age_20s_ratio`, `age_30s_ratio`, `age_40plus_ratio`에서 계산
- 학습 데이터에는 생성되지만, 모델 피처에서는 제거됨 (예측 시점에 알 수 없는 사후 지표)

---

## 5. FEATURE_COLUMNS (19개)

이 섹션이 피처 컬럼의 **단일 출처(Single Source of Truth)**이다.

```python
FEATURE_COLUMNS = [
    # --- 시계열 (5) ---
    "lag_1w", "lag_2w", "lag_4w", "lag_8w",
    "rolling_mean_4w",
    # --- 날짜/분야 인코딩 (3) ---
    "month_sin", "month_cos", "field_encoded",
    # --- 외부 지표 (2) ---
    "search_volume", "job_count",
    # --- 내부 선행지표 (2) ---
    "consultation_count", "page_views",
    # --- 자격증 일정 (2) ---
    "has_cert_exam", "weeks_to_exam",
    # --- 경쟁사 (2) ---
    "competitor_openings", "competitor_avg_price",
    # --- 계절 이벤트 (3) ---
    "is_vacation", "is_exam_season", "is_semester_start",
]
```

**카테고리별 요약:**

| 카테고리 | 피처명 | 설명 |
|---|---|---|
| 시계열 (5) | `lag_1w`, `lag_2w`, `lag_4w`, `lag_8w`, `rolling_mean_4w` | 과거 수강생 수 + 이동 평균 |
| 날짜/분야 (3) | `month_sin`, `month_cos`, `field_encoded` | 월 순환 인코딩 + 분야 |
| 외부 지표 (2) | `search_volume`, `job_count` | 검색량 + 채용 공고 |
| 내부 선행 (2) | `consultation_count`, `page_views` | 상담 건수 + 웹 조회수 |
| 자격증 (2) | `has_cert_exam`, `weeks_to_exam` | 시험 유무 + 시험까지 주수 |
| 경쟁사 (2) | `competitor_openings`, `competitor_avg_price` | 개강 수 + 평균 수강료 |
| 계절 이벤트 (3) | `is_vacation`, `is_exam_season`, `is_semester_start` | 방학/시험/학기 플래그 |

**FEATURE_COLUMNS 원천 매핑:**

| 피처 | 원천 CSV | 생성 단계 | 설명 |
|------|---------|----------|------|
| `lag_1w` | enrollment_history | transformer | 1주 전 등록 수 |
| `lag_2w` | enrollment_history | transformer | 2주 전 등록 수 |
| `lag_4w` | enrollment_history | transformer | 4주 전 등록 수 |
| `lag_8w` | enrollment_history | transformer | 8주 전 등록 수 |
| `rolling_mean_4w` | enrollment_history | transformer | 4주 이동평균 |
| `month_sin` | enrollment_history (date) | transformer | 월 순환 인코딩 sin |
| `month_cos` | enrollment_history (date) | transformer | 월 순환 인코딩 cos |
| `field_encoded` | enrollment_history (field) | transformer | 분야 숫자 인코딩 |
| `search_volume` | search_trends.csv | merger | 주간 검색량 |
| `job_count` | job_postings.csv | merger | 주간 채용 공고 수 |
| `consultation_count` | consultation_logs.csv | merger | 주간 상담 건수 |
| `page_views` | web_logs.csv | merger | 주간 페이지뷰 |
| `has_cert_exam` | cert_exam_schedule.csv | merger | 시험 월 플래그 |
| `weeks_to_exam` | cert_exam_schedule.csv | merger | 다음 시험까지 주 수 |
| `competitor_openings` | competitor_data.csv | merger | 경쟁 학원 개강 수 |
| `competitor_avg_price` | competitor_data.csv | merger | 경쟁 학원 평균 수강료 |
| `is_vacation` | seasonal_events.csv | merger | 방학 플래그 |
| `is_exam_season` | seasonal_events.csv | merger | 시험 시즌 플래그 |
| `is_semester_start` | seasonal_events.csv | merger | 학기 시작 플래그 |

**제거된 피처:**

| 피처 | 제거 사유 |
|------|----------|
| `cart_abandon_rate` | 학원에 장바구니 개념 없음 (도메인 부적합) -- v2에서 완전 삭제 |
| `conversion_rate` | 타겟(enrollment)과 순환 의존 -- 데이터 누수 위험 |
| `age_group_diversity` | 등록 후에만 계산 가능한 사후 지표 |

**비피처 컬럼 (training_dataset.csv에 포함되지만 모델 학습에 사용되지 않는 컬럼):**

| 컬럼 | 용도 |
|------|------|
| `date` | 시계열 정렬 기준 |
| `field` | 분야별 분리 처리용 |
| `cohort` | 기수 정보 (참고용) |
| `enrollment_count` | **타겟 변수** (예측 대상) |
| `ds`, `y` | Prophet 호환 컬럼 |
| `conversion_rate` | 상담→등록 전환율 (피처에서 제외, 참고용) |
| `age_20s_ratio`, `age_30s_ratio`, `age_40plus_ratio` | 연령대 비율 (인구통계 API에서 사용) |
| `age_group_diversity` | Shannon 엔트로피 (피처에서 제외, 참고용) |
| `purpose_career`, `purpose_hobby`, `purpose_cert` | 목적 분포 (인구통계 API에서 사용) |

---

## 6. 모델 아키텍처

### 6.1 공통 구조 (`base.py`)

```python
class BaseForecaster(ABC):
    def train(df)        # 학습
    def predict(features) # 예측 (스레드 안전 — Lock)
    def evaluate(df)      # TimeSeriesSplit K-Fold → MAPE
    def save(path, ver)   # 저장 + metadata.json 생성
    def load(path, ver)   # 로딩 + 피처 불일치 경고
```

모든 모델은 `BaseForecaster`를 상속하고, 동일한 인터페이스로 동작한다.

**PredictionResult (예측 결과):**
```python
@dataclass
class PredictionResult:
    predicted_enrollment: int     # 예측 등록 인원
    demand_tier: DemandTier       # HIGH / MID / LOW
    confidence_lower: float       # 신뢰구간 하한
    confidence_upper: float       # 신뢰구간 상한
    model_used: str               # "xgboost" / "prophet" / "lstm" / "ensemble(...)"
    mape: float | None            # 모델의 MAPE (평가 후 설정)
```

**피처 안전장치 (base.py):**
- `validate_feature_columns()`: 학습/예측 시 누락 피처가 있으면 `warnings.warn()` 출력
- `warn_feature_mismatch()`: 모델 로딩 시 학습 당시 피처와 현재 FEATURE_COLUMNS 불일치 경고
- `ensure_feature_columns()`: 누락 컬럼을 0으로 채워 shape 보장 (원본 DataFrame 변경 없음)

### 6.2 XGBoost -- 트리 기반 앙상블

**한 줄 요약:** 각 행을 독립적인 피처 벡터로 보고, 결정 트리를 순차적으로 쌓아 오차를 줄여나가는 모델.

```
입력 피처 (19개)                         출력
┌──────────────────────────┐
│ lag_1w~8w, rolling_mean, │
│ month_sin/cos,           │
│ search_volume, job_count,│ ──→ XGBRegressor ──→ enrollment_count (실수)
│ consultation_count,      │                       ↓
│ page_views,              │                    round() → 정수
│ has_cert_exam, weeks_to, │                       ↓
│ competitor_*, seasonal,  │                   classify_demand() → HIGH/MID/LOW
│ field_encoded            │
└──────────────────────────┘
```

**하이퍼파라미터:**
```python
XGBRegressor(
    n_estimators=300,      # 결정 트리 300개를 순차적으로 학습
    max_depth=4,           # 각 트리의 최대 깊이 (과적합 방지)
    learning_rate=0.03,    # 각 트리의 기여도 (작을수록 정교, 느림)
    subsample=0.8,         # 각 트리에 전체 데이터의 80%만 사용
    colsample_bytree=0.8,  # 각 트리에 전체 피처의 80%만 사용
)
```

**XGBoost가 학습하는 방식:**
1. 첫 번째 트리: 전체 데이터의 평균으로 시작
2. 두 번째 트리: 첫 번째 트리의 **잔차(오차)**를 예측
3. 세 번째 트리: 누적 오차의 잔차를 예측
4. ... 300번 반복
5. 최종 예측 = 모든 트리 예측의 합

**왜 XGBoost가 잘 작동하는가:**
- 각 행을 독립적으로 처리하므로 분야 혼합 데이터도 문제없음
- `field_encoded` 피처로 "이 행은 coding이고, coding의 패턴은 이렇다"를 학습
- lag 피처가 시계열 정보를 담고 있어 시간적 패턴도 간접적으로 학습

**피처 중요도 (Feature Importance, 2026-04-10 기준):**

| 피처 | Importance | 해석 |
|------|-----------|------|
| is_vacation | 0.2278 | 방학 여부가 가장 강력한 예측 인자 |
| rolling_mean_4w | 0.2139 | 최근 4주 추세 |
| competitor_openings | 0.1801 | 경쟁 학원 개강 수 |
| is_semester_start | 0.1186 | 학기 시작 여부 |
| job_count | 0.1092 | 채용 공고 수 |
| 나머지 14개 | 각 0.003~0.027 | 보조 역할 |

**MAPE: 16.20%**

### 6.3 Prophet -- 시계열 분해 모델

**한 줄 요약:** 시계열을 트렌드(장기 추세) + 계절성(반복 패턴) + 회귀자(외부 요인)로 분해하여 예측하는 Facebook 개발 모델.

```
y(t) = trend(t) + seasonality(t) + regressors(t) + error(t)

trend:        ───────────/───────── (연간 5% 성장 같은 장기 추세)
                        ↗ changepoint (변화점)

seasonality:  ∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿ (방학=증가, 학기중=감소 반복)

regressors:   search_volume, job_count (추가 외부 정보)
```

**핵심 개념:**

| 개념 | 설명 |
|------|------|
| **트렌드 (trend)** | 시간이 지남에 따른 장기적 변화. 연 5% 성장 같은 것 |
| **변화점 (changepoint)** | 트렌드가 급변하는 시점. Prophet이 자동 감지 |
| **계절성 (seasonality)** | 매년 반복되는 패턴. 푸리에 급수로 모델링 |
| **회귀자 (regressor)** | search_volume, job_count 같은 추가 설명 변수 |

**하이퍼파라미터:**
```python
Prophet(
    seasonality_mode="multiplicative",   # 계절성 효과가 트렌드에 비례
    yearly_seasonality=True,             # 연간 패턴 학습
    weekly_seasonality=False,            # 주간 패턴은 불필요 (데이터 자체가 주간)
    changepoint_prior_scale=0.15,        # 변화점 민감도 (높을수록 유연)
)
```

**분야별 분리 학습:**
```python
# 4개 분야 각각에 독립 Prophet 모델을 학습
self._field_models = {
    "coding":   Prophet().fit(coding_data),    # 261행
    "security": Prophet().fit(security_data),  # 261행
    "game":     Prophet().fit(game_data),      # 261행
    "art":      Prophet().fit(art_data),       # 261행
}
```

Prophet은 **단일 시계열 모델**이다. 4분야를 섞으면 coding→security 경계에서 "급락"으로 오해석한다. 분야별 분리가 필수.

**Prophet이 요구하는 데이터 형식:**
```
ds (datetime): 날짜
y (float):     예측 대상 값
+ 선택적 회귀자 컬럼
```

**MAPE: 45.44%** -- 다른 모델보다 높은 이유:
- 주간 등록이 0~8명 정도의 작은 정수 -- MAPE가 구조적으로 불리
- multiplicative 모드에서 0에 가까운 값은 계절성 효과가 왜곡됨

### 6.4 LSTM -- 순환 신경망

**한 줄 요약:** 과거 8주의 시퀀스 패턴을 학습하여 다음 주 등록 인원을 예측하는 딥러닝 모델.

```
입력 시퀀스 (8주 × 19피처)               LSTM 셀                    출력

주 t-8:  [lag_1w, lag_2w, ...]  → ┌──────────┐
주 t-7:  [lag_1w, lag_2w, ...]  → │          │
주 t-6:  [lag_1w, lag_2w, ...]  → │   LSTM   │
    ...                           │  2 layers │ → h(마지막) → Linear → enrollment
주 t-2:  [lag_1w, lag_2w, ...]  → │ hidden=32 │                        (1개 값)
주 t-1:  [lag_1w, lag_2w, ...]  → │ dropout=0.2│
                                  └──────────┘
```

**LSTM이 학습하는 방식:**

1. **시퀀스 생성 (슬라이딩 윈도우):**
   ```
   데이터: [w1, w2, w3, w4, w5, w6, ..., w9, w10, ...]

   시퀀스 1: [w1~w8]  → 정답: w9
   시퀀스 2: [w2~w9]  → 정답: w10
   시퀀스 3: [w3~w10] → 정답: w11
   ...
   ```
   8주 분량의 데이터를 입력으로, 바로 다음 주 값을 예측

2. **LSTM 셀 내부 (직관적 이해):**
   - **잊기 게이트:** "2달 전의 정보는 잊어도 되나?" -- sigmoid로 판단
   - **입력 게이트:** "이번 주 정보 중 뭘 기억해야 하나?" -- sigmoid로 판단
   - **셀 상태:** 장기 기억 (계절성 같은 느린 패턴)
   - **은닉 상태:** 단기 기억 (최근 몇 주의 추세)

3. **2층 구조:** 첫 번째 LSTM이 추출한 패턴을 두 번째 LSTM이 더 추상적으로 학습

**현재 하이퍼파라미터 (단일 출처):**

| 파라미터 | 값 | 비고 |
|---|---|---|
| `SEQUENCE_LENGTH` | 8 | 8주(2개월) 시퀀스 |
| `HIDDEN_SIZE` | 32 | 소규모 데이터 최적화 |
| `NUM_LAYERS` | 2 | 2층 LSTM |
| `DROPOUT` | 0.2 | |
| `INPUT_SIZE` | 19 | `len(FEATURE_COLUMNS)` -- 동적 |
| `PATIENCE` | 15 | Early stopping |
| `SCHEDULER_PATIENCE` | 5 | LR 감소 전 대기 |
| `learning_rate` | 5e-4 | |
| `epochs` | 200 | |

**학습 안정화 (Early Stopping + LR Scheduler):**

- **Early Stopping:** 검증 손실이 `PATIENCE`(15) 에포크 연속 미개선 시 학습 종료하여 과적합 방지
- **ReduceLROnPlateau:** 검증 손실이 `SCHEDULER_PATIENCE`(5) 에포크 미개선 시 학습률을 자동 감소하여 미세 조정
- 최대 에포크 200으로 설정, 실제로는 Early Stopping이 불필요한 학습을 자동 차단

**Feature-aware 데이터 증강:**
```python
# 이름 기반 동적 분류 (하드코딩 인덱스 사용 금지)
_PROTECTED_NAMES = {
    "month_sin", "month_cos", "field_encoded",
    "has_cert_exam", "is_vacation", "is_exam_season", "is_semester_start",
}

# 보호 피처: 이산값/바이너리 → 원본 유지 (7개)
PROTECTED_FEATURES = [i for i, c in enumerate(FEATURE_COLUMNS) if c in _PROTECTED_NAMES]

# 증강 대상: 연속값 → jittering + scaling 적용 (12개)
AUGMENTABLE_FEATURES = [i for i, c in enumerate(FEATURE_COLUMNS) if c not in _PROTECTED_NAMES]
```

증강 방식:
- **Jittering:** 연속값 피처에 가우시안 노이즈(sigma=0.02) 추가
- **Scaling:** 시퀀스별 동일 배율(0.95~1.05)로 연속값 피처 스케일링
- 타겟(y)도 같은 비율로 스케일링 (lag 피처가 과거 타겟의 시차이므로 일관성 유지)
- 결과: 원본의 3배 시퀀스 (원본 + 2개 증강본)

**왜 보호 피처를 증강하면 안 되는가:**
- `month_sin/cos`를 jittering하면 "3.5월" 같은 존재하지 않는 시점이 생성
- `field_encoded`를 스케일링하면 "coding과 security 사이" 같은 의미 없는 분야가 됨
- `is_vacation`, `has_cert_exam` 등 바이너리 플래그에 노이즈를 더하면 0/1이 아닌 값이 됨

**분야별 시퀀스 생성:**
```python
# 변경 전: 전체 데이터에서 시퀀스 생성 → 분야 경계 오염
[...coding w416, coding w417, security w1, security w2...]
                              ↑ 경계: coding 끝 → security 시작이 하나의 시퀀스에 섞임

# 변경 후: 분야별로 독립 시퀀스 생성
coding:   [w1~w8]→w9, [w2~w9]→w10, ...  (409개 시퀀스)
security: [w1~w8]→w9, [w2~w9]→w10, ...  (409개 시퀀스)
game:     ...
art:      ...
→ 총 ~1636개 시퀀스 (원본)
→ 증강 후 ~4908개 시퀀스 (원본 × 3)로 학습
```

**데이터 규모별 하이퍼파라미터 가이드:**

| 데이터 규모 | HIDDEN_SIZE | SEQUENCE_LENGTH | NUM_LAYERS | DROPOUT |
|---|---|---|---|---|
| ~1,700행 (현재) | 32 | 8 | 2 | 0.2 |
| 5,000+ 행 | 64 | 12 | 2 | 0.3 |
| 10,000+ 행 | 128 | 16 | 2~3 | 0.3 |
| 50,000+ 행 | 256 | 24 | 3 | 0.3~0.4 |

**MAPE: 40.32%**

---

## 7. 앙상블 & 평가

### 7.1 앙상블 (`ensemble.py`)

```python
class EnsembleForecaster:
    # 여러 모델의 예측을 가중 평균
    예측 = w1 × XGBoost예측 + w2 × Prophet예측 + w3 × LSTM예측
```

**가중치 자동 설정:**
```python
# MAPE 역수 비례 — MAPE가 낮을수록 높은 가중치
auto_weight():
    XGBoost MAPE=16.20% → weight = 1/16.20 = 0.062 → 정규화 후 ~52%
    LSTM    MAPE=40.32% → weight = 1/40.32 = 0.025 → 정규화 후 ~21%
    Prophet MAPE=45.44% → weight = 1/45.44 = 0.022 → 정규화 후 ~18%
```

**신뢰구간:** 보수적으로 설정
- 하한 = 모든 모델 중 `min(confidence_lower)`
- 상한 = 모든 모델 중 `max(confidence_upper)`

### 7.2 TimeSeriesSplit K-Fold

**왜 일반 K-Fold를 쓰면 안 되는가:**

```
일반 K-Fold (랜덤 섞기):
  Train: [1월, 5월, 9월, 3월]  ← 미래(9월) 데이터로 학습
  Test:  [7월]                 ← 과거(7월)을 예측?? → 데이터 누수!

시계열 K-Fold (TimeSeriesSplit):
  Fold 1 Train: [1월~6월]   Test: [7월~8월]     ✓ 과거→미래
  Fold 2 Train: [1월~8월]   Test: [9월~10월]    ✓ 과거→미래
  Fold 3 Train: [1월~10월]  Test: [11월~12월]   ✓ 과거→미래
```

시계열 데이터에서 랜덤 셔플은 **미래 정보가 학습에 포함**되는 데이터 누수를 일으킨다. 항상 과거 데이터로 학습하고 미래를 예측해야 한다.

**MAPE (Mean Absolute Percentage Error):**

```
MAPE = mean( |실제 - 예측| / 실제 ) × 100%
```

| MAPE | 해석 |
|------|------|
| < 10% | 매우 정확 |
| 10~20% | 양호 |
| 20~30% | 합리적 |
| 30~50% | 부정확 |
| > 50% | 비실용적 |

**MAPE의 한계:** 실제값이 작을수록 분모가 작아져 MAPE가 과대 평가된다.
- 실제=20, 예측=19 -- MAPE 5%
- 실제=2, 예측=1 -- MAPE 50% (같은 1명 오차인데 10배)

### 7.3 현재 MAPE 결과

| 모델 | MAPE | 데이터 | 평가 |
|------|------|--------|------|
| **XGBoost** | **16.20%** | 1668행, 19피처 | 양호 |
| **LSTM** | **40.32%** | 1668행, 증강 적용 | 합리적 |
| **Prophet** | **45.44%** | 분야별 분리, 회귀자 2개 | 부정확 -- 소수값에서 MAPE 불리 |

> 합성 데이터 특성상 MAPE는 실데이터 대비 낙관적으로 편향됨.

---

## 8. 디바이스 전략

```python
def get_device():
    if torch.cuda.is_available():   return "cuda"    # GPU 서버 (향후)
    elif torch.backends.mps.is_available(): return "mps"  # M4 MacBook
    else:                           return "cpu"      # Droplet
```

| | M4 MacBook (로컬) | Droplet (서버) |
|---|---|---|
| **역할** | LSTM 학습, 실험 | XGBoost/Prophet 자동 재학습, API 서빙 |
| **가속기** | MPS (Apple Silicon GPU) | CPU only |
| **사양** | M4, 통합메모리 | 1 vCPU / 2GB RAM |

**LSTM 학습 워크플로우:**
```
M4 MacBook에서 학습
    ↓
model/saved/lstm/v1/model.pt 생성
    ↓
scp로 Droplet 전송
    ↓
Droplet에서 load() → predict() 만 사용
```

Droplet(2GB RAM)은 LSTM 학습 불가. 추론만 가능.

---

## 9. 합성 상관 관계 경고

`internal_generator.py`와 `events_generator.py`의 일부 생성기는 `enrollment_df`에서 값을 파생시킨다. 이로 인해 **합성 데이터 간 인위적 상관 관계 (synthetic correlation inflation)**가 발생한다:

- 생성기가 심어놓은 패턴을 모델이 재발견하는 **자기순환 구조**
- 실제 데이터의 불규칙성을 완전히 재현할 수 없음
- MAPE 수치는 실제 예측 성능보다 낙관적으로 편향됨

**파생 생성기** (enrollment 기반, 상관 관계 존재):
- `generate_search_trends()` -- 선행 2~4주
- `generate_job_postings()` -- 동행
- `generate_consultation_logs()` -- 선행 1~2주
- `generate_student_profiles()` -- 동행 (Dirichlet 분포)
- `generate_web_logs()` -- 선행 1~3주
- `generate_competitor_data()` -- 동행

**결정론적 생성기** (캘린더 기반, 상관 관계 없음):
- `generate_cert_exam_schedule()` -- 자격증 시험 일정
- `generate_seasonal_events()` -- 계절성 이벤트

실 서비스 투입 전 반드시 **실제 학원 데이터로 재학습 및 재평가**가 필요하다.

---

## 10. 실제 데이터 전환 가이드

합성 데이터와 동일한 형식의 실제 데이터가 확보되면, 생성기를 교체하지 않고 CSV 파일만 대체하면 된다.

### 필요한 실제 데이터 형식

**수강 이력 (enrollment_history.csv) -- 필수:**
```csv
date,field,cohort,enrollment_count,ds,y
2024-01-08,coding,1,7,2024-01-08,7
2024-01-15,coding,1,5,2024-01-15,5
```

**검색 트렌드 (search_trends.csv):**
```csv
date,field,search_volume,ds,y
2024-01-08,coding,12,2024-01-08,12
```

**채용 공고 (job_postings.csv):**
```csv
date,field,job_count,ds,y
2024-01-08,coding,15,2024-01-08,15
```

**상담 로그 (consultation_logs.csv):**
```csv
date,field,consultation_count,conversion_rate,ds,y
2024-01-08,coding,18,0.22,2024-01-08,18
```

**학생 프로필 (student_profiles.csv):**
```csv
date,field,age_20s_ratio,age_30s_ratio,age_40plus_ratio,purpose_career,purpose_hobby,purpose_cert,ds,y
2024-01-08,coding,0.55,0.32,0.13,0.60,0.22,0.18,2024-01-08,7
```

**웹/앱 로그 (web_logs.csv):**
```csv
date,field,page_views,ds,y
2024-01-08,coding,85,2024-01-08,85
```

**자격증 시험 일정 (cert_exam_schedule.csv):**
```csv
date,field,has_cert_exam,weeks_to_exam,ds,y
2024-01-08,coding,0,10,2024-01-08,10
```

**경쟁 학원 데이터 (competitor_data.csv):**
```csv
date,field,competitor_openings,competitor_avg_price,ds,y
2024-01-08,coding,5,520000,2024-01-08,5
```

**계절성 이벤트 (seasonal_events.csv) -- field 없음:**
```csv
date,is_vacation,is_exam_season,is_semester_start
2024-01-08,1,0,0
```

### 전환 절차

1. 실제 CSV 파일을 `data/raw/internal/`, `data/raw/external/`에 배치
2. `run_all.py`의 생성 단계를 건너뛰거나 비활성화
3. training_dataset.csv 재생성:
   ```bash
   .venv/bin/python -c "from edupulse.preprocessing.merger import build_training_dataset; build_training_dataset()"
   ```
4. 모델 재학습:
   ```bash
   .venv/bin/python -m edupulse.model.train --model all --version 1
   ```
5. MAPE 재평가 후 수요 임계값(`constants.py`의 `DEMAND_THRESHOLDS`)을 실제 스케일에 맞게 재조정

### 유의사항

- 실제 데이터의 결측 패턴은 합성 데이터보다 불규칙할 수 있음 -- `cleaner.py`의 보간 로직 검토 필요
- 분야별 수요 규모가 합성 데이터와 다를 경우 임계값 재설정 필수
- 실제 검색 트렌드는 Naver DataLab API나 Google Trends API로 수집
- 실제 채용 공고는 크롤러(`collection/crawlers/job_posting.py`)로 수집
- 일부 CSV(상담 로그, 웹 로그, 학생 프로필 등)가 없어도 merger가 graceful하게 건너뜀 -- 해당 피처는 0으로 채워짐

---

## 11. 용어 정리

| 용어 | 설명 |
|------|------|
| **lag feature** | 과거 시점의 값을 현재 행의 피처로 사용. lag_1w = 1주 전 값 |
| **rolling mean** | 이동평균. 최근 N개 값의 평균으로 노이즈를 평활화 |
| **순환 인코딩** | 월(1~12)을 sin/cos로 변환. 12월→1월의 연속성 보장 |
| **changepoint** | Prophet에서 트렌드가 급변하는 시점 |
| **시퀀스 (LSTM)** | 연속된 N주의 데이터를 하나의 입력으로 묶은 것 |
| **MinMaxScaler** | 값을 0~1 범위로 정규화. 신경망 학습에 필수 |
| **TimeSeriesSplit** | 시간 순서를 유지한 K-Fold. 과거→미래 방향으로만 분할 |
| **MAPE** | 평균 절대 백분율 오차. 예측 정확도의 퍼센트 지표 |
| **IQR** | 사분위범위(Q3-Q1). 이상치 탐지의 기준 |
| **forward fill** | 결측치를 직전 유효값으로 채우는 방법 |
| **앙상블** | 여러 모델의 예측을 조합하여 더 안정적인 결과를 얻는 기법 |
| **Dropout** | 학습 시 일부 뉴런을 랜덤 비활성화하여 과적합 방지 |
| **Early Stopping** | 검증 손실이 개선되지 않으면 학습을 조기 종료하여 과적합 방지 |
| **ReduceLROnPlateau** | 검증 손실 정체 시 학습률을 자동 감소시키는 스케줄러 |
| **데이터 증강** | 원본 데이터에 노이즈/스케일링을 적용하여 학습 데이터를 인위적으로 확대 |
| **Gradient Boosting** | XGBoost의 핵심 원리. 이전 트리의 오차를 다음 트리가 보정 |
| **Feature Importance** | 트리 모델에서 각 피처가 예측에 기여하는 정도 (gain 기준) |
| **data leakage** | 예측 시점에 알 수 없는 정보가 피처에 포함되어 낙관적 편향 유발 |
| **synthetic correlation** | 합성 데이터가 동일 소스에서 파생되어 인위적으로 높은 상관 발생 |

---

## 12. 부록: 모델 레이어 리팩토링 이력

모델 레이어의 구조적 문제 8가지 중 5가지를 수정한 작업 기록.
기존 ModelMetadata 시스템(10/12 테스트 통과) 위에 진행되었으며,
Prophet `stan_backend` 2개 실패는 기존 의존성 버그로 이 작업과 무관하다.

### 12.1 앙상블 서브모델 thread lock 우회 방지

**커밋**: `3468113` -- `fix: 앙상블 서브모델 thread lock 우회 방지`

**문제:** `EnsembleForecaster._predict()`가 서브모델의 `model._predict(features)`를 직접 호출하고 있었다. `BaseForecaster`는 `predict()` 메서드 안에서 `threading.Lock`을 잡고 `_predict()`를 호출하는 구조인데, 앙상블이 `_predict()`를 직접 호출하면 이 lock을 완전히 우회하게 된다. 멀티스레드 환경(FastAPI 등)에서 서브모델 내부 상태가 동시 접근에 의해 손상될 수 있는 버그였다.

**변경:**

| 파일 | 내용 |
|---|---|
| `edupulse/model/ensemble.py` | line 143: `model._predict(features)` → `model.predict(features)` |
| `tests/test_model.py` | `test_ensemble_uses_public_predict` 추가 -- mock으로 public `predict()` 호출 검증 |

**영향:** 서브모델 예측 시 thread lock이 정상 동작하여 동시 요청 안전성 확보. 기존 테스트 전부 통과 유지.

### 12.2 피처 컬럼 누락 시 경고 로그 추가

**커밋**: `a147359` -- `feat: 피처 컬럼 누락 시 경고 로그 추가`

**문제:** XGBoost, LSTM, Prophet 모델 모두 `[c for c in FEATURE_COLUMNS if c in df.columns]` 패턴으로 누락된 피처 컬럼을 조용히 무시하고 있었다. 학습/예측 데이터에 컬럼이 빠져도 에러 없이 진행되므로, 성능 저하의 원인을 추적하기 어려웠다.

**변경:**

| 파일 | 내용 |
|---|---|
| `edupulse/model/base.py` | `validate_feature_columns()` 헬퍼 함수 추가 -- 누락 시 `warnings.warn()` + `logger.warning()` |
| `edupulse/model/xgboost_model.py` | 3곳 (`train`, `_predict`, `evaluate`) 교체 |
| `edupulse/model/lstm_model.py` | 3곳 (`_build_sequences_per_field`, `_prepare_arrays`, `_predict`) 교체 |
| `edupulse/model/prophet_model.py` | 4곳 (`_to_prophet_df`, `train` x2, `evaluate` x2) 교체 |
| `tests/test_model.py` | `test_missing_columns_warns` 추가 -- 누락 시 경고 발생 및 전체 존재 시 경고 없음 검증 |

**영향:** 피처 컬럼이 누락되면 로그와 경고로 즉시 확인 가능. 기존 동작(누락 컬럼 제외 후 진행)은 그대로 유지하여 하위 호환성 보존.

### 12.3 모델 로딩 이중 캐시 통합 및 버전 불일치 해소

**커밋**: `2293182` -- `refactor: 모델 로딩 이중 캐시 통합 및 버전 불일치 해소`

**문제:** 모델 로딩 경로가 두 곳에 존재했다:
1. `api/dependencies.py`: `MODEL_REGISTRY` dict + `load_models()` -- version=1 하드코딩
2. `model/predict.py`: `_model_cache` dict + `_load_model()` -- version=2 기본값

동일 요청이 코드 경로에 따라 다른 캐시, 다른 모델 버전을 사용할 수 있는 구조적 결함이었다. 또한 `_build_features`와 `_load_model`이 private 함수(`_` prefix)인데 외부 모듈에서 직접 import하고 있었다.

**변경:**

| 파일 | 내용 |
|---|---|
| `edupulse/model/predict.py` | `_load_model` → `load_model`, `_build_features` → `build_features` public 전환. `MODEL_VERSION = 1` 상수 추가. `clear_model_cache()` 추가 |
| `edupulse/api/dependencies.py` | 자체 `MODEL_REGISTRY` 제거, `predict.load_model()`에 위임. `get_loaded_model_names()` 추가 |
| `edupulse/api/routers/demand.py` | import 경로 `_build_features` → `build_features` |
| `edupulse/api/routers/health.py` | `MODEL_REGISTRY` → `get_loaded_model_names()` |
| `tests/conftest.py` | `MODEL_REGISTRY` → `_model_cache` 직접 참조 |
| `tests/test_demand.py` | 동일 변경 |

**영향:** 모델 캐시가 `predict._model_cache` 한 곳으로 통합되어 버전 불일치 불가. `MODEL_VERSION` 상수로 버전 관리 단일화. API와 직접 호출 경로가 동일한 캐시를 공유.

### 12.4 LSTM 평가 메서드 중복 코드 추출

**커밋**: `77bf150` -- `refactor: LSTM 평가 메서드 중복 코드 추출`

**문제:** `LSTMForecaster._evaluate_single()` (약 75줄)과 `_evaluate_per_field()` (약 75줄)의 K-Fold 학습/평가 루프가 거의 동일한 코드를 복사-붙여넣기하고 있었다. 한쪽을 수정하면 다른 쪽도 동일하게 수정해야 하는 유지보수 리스크가 있었다.

**변경:**

| 파일 | 내용 |
|---|---|
| `edupulse/model/lstm_model.py` | `_evaluate_fold(X_raw, y_raw, n_splits)` 헬퍼 추출. `_evaluate_single`과 `_evaluate_per_field`를 각 5줄 이하로 단순화. 총 81줄 제거, 28줄 추가 |

**영향:** 평가 로직 변경 시 한 곳만 수정하면 됨. 동작은 완전히 동일 (동일 결과 보장).

### 12.5 course_name 필드 미사용 상태 문서화

**커밋**: `58f26de` -- `docs: course_name 필드 미사용 상태 문서화`

**문제:** `DemandRequest.course_name`과 `build_features(course_name, ...)`의 `course_name` 파라미터가 실제 모델 예측에 전혀 사용되지 않는데, 이 사실이 코드에서 드러나지 않았다. API 사용자나 새 개발자가 이 필드가 예측에 영향을 준다고 오해할 수 있었다.

**변경:**

| 파일 | 내용 |
|---|---|
| `edupulse/api/schemas/demand.py` | `course_name` 필드에 미사용 상태 주석 추가 |
| `edupulse/model/predict.py` | `build_features()` docstring에 미사용 상태 명시 |

**영향:** 코드 변경 없음 (주석만 추가). 향후 과정별 세분화 시 활용 예정임을 명시.

### 범위 밖 (별도 브랜치 대상)

아래 항목은 이번 작업에서 제외했으며, 별도 브랜치에서 진행해야 한다:

- `FEATURE_COLUMNS`를 `constants.py`로 이동 -- 영향 파일이 많아 별도 리팩토링 필요
- Prophet `stan_backend` 호환성 수정 -- 의존성 업그레이드 필요
- 모델 버전 자동 감지 (`saved/` 디렉토리 스캔) -- 설계 결정 필요

### 테스트 결과

```
22 passed, 2 failed (Prophet stan_backend 기존 버그)
```

- 기존 10개 테스트 + 새 테스트 2개 (`test_missing_columns_warns`, `test_ensemble_uses_public_predict`) = 12개 모델 테스트
- API/health 테스트 10개 전부 통과

---

## 13. 파일 맵

```
edupulse/
├── constants.py                    # 수요 등급 기준 + CSV 경로 상수 9개
│
├── data/generators/
│   ├── enrollment_generator.py     # 주간 수강 이력 합성
│   │   ├── BASE_WEEKLY_ENROLLMENT  # 분야별 기본 수요
│   │   ├── WEEKLY_SEASONAL_FACTOR  # 월별 계절성 보정
│   │   ├── _compute_trend()        # 연도별 트렌드 승수
│   │   └── generate_enrollment_history()
│   │
│   ├── external_generator.py       # 외부 지표 생성 (파생)
│   │   ├── SEARCH_CORRELATION      # 검색량 상관 계수
│   │   ├── JOB_CORRELATION         # 채용 공고 상관 계수
│   │   ├── generate_search_trends()
│   │   └── generate_job_postings()
│   │
│   ├── internal_generator.py       # 내부 지표 생성 (파생)
│   │   ├── CONSULT_MULTIPLIER      # 분야별 상담 배율
│   │   ├── FIELD_AGE_ALPHA         # 연령대 Dirichlet alpha
│   │   ├── FIELD_PURPOSE_ALPHA     # 수강 목적 Dirichlet alpha
│   │   ├── PV_MULTIPLIER           # 페이지뷰 배율
│   │   ├── generate_consultation_logs()
│   │   ├── generate_student_profiles()
│   │   └── generate_web_logs()
│   │
│   ├── events_generator.py         # 이벤트/외부환경 생성
│   │   ├── CERT_EXAM_MONTHS        # 분야별 시험 월
│   │   ├── COMP_RATIO              # 경쟁 학원 상관 계수
│   │   ├── BASE_PRICE              # 분야별 기준 수강료
│   │   ├── _weeks_to_next_exam()   # 다음 시험까지 주 수
│   │   ├── generate_cert_exam_schedule()
│   │   ├── generate_competitor_data()
│   │   └── generate_seasonal_events()
│   │
│   └── run_all.py                  # 전체 생성 오케스트레이터
│       └── run(n_years=8, start_year=2018)  # 9개 CSV 생성
│
├── preprocessing/
│   ├── merger.py                   # 9개 CSV → 병합 DataFrame
│   │   ├── merge_datasets()        # [field, date] LEFT JOIN
│   │   └── build_training_dataset()# raw → merge → clean → transform → CSV 저장
│   │
│   ├── cleaner.py                  # 결측치 보간 + IQR 이상치 클리핑
│   │   └── clean_data()
│   │
│   └── transformer.py              # lag, 순환 인코딩, 파생 피처
│       ├── add_lag_features()      # lag_1w~8w, rolling_mean_4w, month_sin/cos, field_encoded, age_group_diversity
│       ├── compute_month_encoding()# 월 → (sin, cos)
│       └── compute_field_encoding()# 분야 → 숫자
│
├── model/
│   ├── base.py                     # BaseForecaster ABC + PredictionResult + 피처 검증
│   ├── utils.py                    # get_device() (MPS/CUDA/CPU 감지)
│   ├── xgboost_model.py            # XGBRegressor 래퍼 + FEATURE_COLUMNS 정의 (19개)
│   ├── prophet_model.py            # Prophet 래퍼, 분야별 개별 학습
│   ├── lstm_model.py               # LSTM 래퍼, 분야별 시퀀스 + 증강 + Early Stopping
│   ├── ensemble.py                 # MAPE 역수 가중 앙상블
│   ├── predict.py                  # build_features() + predict_demand() + 모델 캐시
│   ├── train.py                    # 학습 CLI
│   ├── evaluate.py                 # 평가 CLI (MAPE 비교)
│   ├── retrain.py                  # 자동 재학습 스케줄러
│   └── saved/                      # 저장된 모델 (xgboost/v1/, prophet/v1/, lstm/v1/)
│
├── api/
│   ├── main.py                     # FastAPI 진입점 (5개 라우터 등록)
│   ├── dependencies.py             # 모델 DI (get_model)
│   ├── middleware.py                # CORS 설정
│   ├── routers/
│   │   ├── demand.py               # 수요 예측 + 폐강 위험 (2 endpoints)
│   │   ├── schedule.py             # 강사/강의실 배정 (1 endpoint)
│   │   ├── marketing.py            # 마케팅 타이밍 + 전환 예측 (2 endpoints)
│   │   ├── simulation.py           # 시뮬레이션 4종 (4 endpoints)
│   │   └── health.py               # 헬스체크 (1 endpoint)
│   ├── schemas/
│   │   ├── demand.py               # DemandRequest/Response + ClosureRisk
│   │   ├── schedule.py             # ScheduleRequest/Response + AssignmentPlan
│   │   ├── marketing.py            # MarketingRequest/Response + LeadConversion
│   │   └── simulation.py           # OptimalStart, Simulate, Demographics, Competitor
│   └── services/
│       ├── simulation_service.py   # optimal-start, simulate, demographics, competitors
│       ├── marketing_service.py    # lead-conversion 전환 예측
│       └── schedule_service.py     # assignment_plan 배정 계획
│
└── data/warehouse/
    └── training_dataset.csv        # 최종 학습 데이터 (1668행, 피처 19개 + 비피처 15개)

scripts/
└── run_pipeline.py                 # 생성 → 전처리 → 학습 전체 파이프라인

tests/
├── conftest.py                     # FakeForecaster + make_fake_forecaster 팩토리
├── test_model.py                   # 모델 학습/예측/평가 테스트 (30+)
├── test_preprocessing.py           # 전처리 모듈 테스트
├── test_generators.py              # 합성 데이터 생성기 테스트
├── test_demand.py                  # demand + marketing + schedule API 테스트
├── test_simulation.py              # simulation 4종 API 테스트
├── test_collection.py              # 데이터 수집 테스트
└── test_health.py                  # 헬스체크 테스트
```
