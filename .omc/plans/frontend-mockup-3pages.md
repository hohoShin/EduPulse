# 프론트엔드 Mock 페이지 3종 구현 계획

**Date:** 2026-04-10
**Branch:** `feat/frontend-mockup-pages` (from `dev`)
**Phase:** A (Mock 데이터 기반, 백엔드 연동 없음)

---

## 요약

기존 프론트엔드 (Dashboard + Simulator)에 3개 페이지를 추가한다:
1. **마케팅 분석** — 잠재 수강생 전환 예측 + 광고 타이밍 추천
2. **운영 관리** — 폐강 위험도 평가 + 강사/강의실 배정
3. **시장 분석** — 수강생 인구통계 + 경쟁 학원 동향 + 최적 개강일 추천

기존 패턴 준수:
- mockAdapter.js + fixtures/ 로 Mock 데이터 제공
- 순수 CSS 변수 + 인라인 스타일 (Tailwind 없음)
- Recharts로 차트 렌더링
- useState + useEffect로 상태 관리
- 한국어 UI, 영어 필드명

---

## 사이드바 메뉴 (변경 후)

```
├── 대시보드         /                (기존)
├── 시뮬레이터       /simulator       (기존)
├── 마케팅 분석      /marketing       (신규)
├── 운영 관리        /operations      (신규)
└── 시장 분석        /market          (신규)
```

---

## 페이지 1: 마케팅 분석 (/marketing)

### 1.1 상단: 분야 선택 드롭다운
- coding / security / game / art 중 선택 (기본값: coding)
- 선택 시 하단 두 섹션 모두 갱신

### 1.2 섹션 A: 잠재 수강생 전환 예측 (lead-conversion)
**대응 API:** `POST /marketing/lead-conversion`

| 요소 | 설명 |
|------|------|
| 예상 전환 수 | 큰 숫자 + TierBadge 스타일 카드 |
| 전환율 추세 차트 | Recharts LineChart — 최근 8주 전환율 (%) |
| 상담 건수 추세 차트 | Recharts BarChart — 최근 8주 상담 건수 |
| 추천 액션 | 리스트 형태로 recommendations 표시 |

**Mock 데이터 예시:**
```js
{
  field: "coding",
  estimated_conversions: 42,
  conversion_rate_trend: [0.32, 0.35, 0.33, 0.38, 0.36, 0.40, 0.39, 0.42],
  consultation_count_trend: [120, 115, 130, 125, 140, 135, 150, 145],
  recommendations: [
    "전환율이 상승 추세입니다. 현재 마케팅 전략을 유지하세요.",
    "상담 후 미등록 고객에 대한 후속 연락을 강화하세요.",
    "얼리버드 할인으로 조기 등록을 유도하세요."
  ]
}
```

### 1.3 섹션 B: 광고 타이밍 추천 (marketing/timing)
**대응 API:** `POST /marketing/timing`

| 요소 | 설명 |
|------|------|
| 수요 등급별 3컬럼 카드 | High / Mid / Low 각각의 추천 값 |
| 광고 시작 시기 | N주 전 (타임라인 비주얼) |
| 얼리버드 기간 | N일 (진행 바) |
| 할인율 | N% (강조 텍스트) |

**Mock 데이터:**
```js
[
  { demand_tier: "High", ad_launch_weeks_before: 2, earlybird_duration_days: 7, discount_rate: 0.05 },
  { demand_tier: "Mid",  ad_launch_weeks_before: 3, earlybird_duration_days: 14, discount_rate: 0.10 },
  { demand_tier: "Low",  ad_launch_weeks_before: 4, earlybird_duration_days: 21, discount_rate: 0.15 },
]
```

---

## 페이지 2: 운영 관리 (/operations)

### 2.1 상단: 강좌 정보 입력 폼
- 강좌명 (text), 분야 (select), 시작일 (date) — Simulator와 유사한 폼

### 2.2 섹션 A: 폐강 위험도 평가 (closure-risk)
**대응 API:** `POST /demand/closure-risk`

| 요소 | 설명 |
|------|------|
| 위험도 게이지 | risk_score (0~1) 원형 게이지 또는 진행 바, 색상으로 등급 표시 |
| 위험 등급 배지 | high(빨강) / medium(노랑) / low(초록) |
| 위험 요인 리스트 | contributing_factors 항목별 표시 |
| 권장 조치 | recommendation 텍스트 카드 |

**Mock 데이터:**
```js
{
  risk_score: 0.72,
  risk_level: "high",
  contributing_factors: [
    "예측 수강생 수 부족: 3명 (LOW 등급)",
    "신뢰 구간 하한(1.5명)이 최소 개강 인원(5명) 미만"
  ],
  recommendation: "마케팅 강화 및 조기 등록 할인 적용을 권장합니다. 개강 4주 전까지 최소 인원 미달 시 폐강을 검토하세요."
}
```

### 2.3 섹션 B: 강사/강의실 배정 계획 (schedule/suggest)
**대응 API:** `POST /schedule/suggest`

| 요소 | 설명 |
|------|------|
| 요약 카드 | 필요 강사 수, 필요 강의실 수 (아이콘 + 숫자) |
| 배정 테이블 | assignment_plan.classes — 반별 강사/시간/강의실 테이블 |
| 배정 요약 | assignment_plan.summary 텍스트 |

**Mock 데이터:**
```js
{
  course_name: "Python 웹개발",
  required_instructors: 2,
  required_classrooms: 1,
  assignment_plan: {
    classes: [
      { class_name: "A반", instructor_slot: "강사 1", time_slot: "오전 (09:00-12:00)", classroom: "강의실 1" },
      { class_name: "B반", instructor_slot: "강사 2", time_slot: "오후 (13:00-16:00)", classroom: "강의실 1" }
    ],
    summary: "30명 기준: 2개 반 편성 (반당 15명), 강사 2명, 강의실 1개 (오전/오후 분할)"
  }
}
```

---

## 페이지 3: 시장 분석 (/market)

### 3.1 상단: 분야 선택 드롭다운 + 날짜 범위 (최적 개강일용)

### 3.2 섹션 A: 수강생 인구통계 (demographics)
**대응 API:** `POST /simulation/demographics`

| 요소 | 설명 |
|------|------|
| 연령대 분포 | Recharts PieChart 또는 도넛 차트 (20대/30대/40대+) |
| 수강 목적 분포 | Recharts BarChart 가로 (취업/취미/자격증) |
| 트렌드 배지 | "증가" / "안정" / "감소" 텍스트 배지 |

**Mock 데이터:**
```js
{
  field: "coding",
  age_distribution: [
    { group: "20대", ratio: 0.55 },
    { group: "30대", ratio: 0.33 },
    { group: "40대 이상", ratio: 0.12 }
  ],
  purpose_distribution: [
    { purpose: "취업", ratio: 0.56 },
    { purpose: "취미", ratio: 0.22 },
    { purpose: "자격증", ratio: 0.22 }
  ],
  trend: "증가"
}
```

### 3.3 섹션 B: 경쟁 학원 동향 (competitors)
**대응 API:** `POST /simulation/competitors`

| 요소 | 설명 |
|------|------|
| 경쟁사 개강 수 | 큰 숫자 카드 |
| 평균 수강료 | 만원 단위 표시 |
| 포화도 지수 게이지 | saturation_index (0~2) 게이지 바 |
| 전략 추천 | recommendation 텍스트 카드 |

**Mock 데이터:**
```js
{
  field: "coding",
  competitor_openings: 8,
  competitor_avg_price: 1200000,
  saturation_index: 1.2,
  recommendation: "경쟁이 활발합니다. 가격 경쟁력 또는 강사 전문성 강화를 권장합니다."
}
```

### 3.4 섹션 C: 최적 개강일 추천 (optimal-start)
**대응 API:** `POST /simulation/optimal-start`

| 요소 | 설명 |
|------|------|
| 상위 5개 후보 카드 | 날짜, 예상 수강생, 수요 등급, 종합 점수를 카드로 나열 |
| 종합 점수 바 | composite_score 가로 바 (0~1) |
| 1위 강조 | 첫 번째 카드에 "추천" 배지 |

**Mock 데이터:**
```js
{
  top_candidates: [
    { date: "2026-07-06", predicted_enrollment: 7, demand_tier: "High", composite_score: 0.85 },
    { date: "2026-07-13", predicted_enrollment: 6, demand_tier: "High", composite_score: 0.78 },
    { date: "2026-06-29", predicted_enrollment: 5, demand_tier: "Mid",  composite_score: 0.65 },
    { date: "2026-07-20", predicted_enrollment: 5, demand_tier: "Mid",  composite_score: 0.60 },
    { date: "2026-06-22", predicted_enrollment: 4, demand_tier: "Mid",  composite_score: 0.52 },
  ]
}
```

---

## 파일 변경 목록

### 신규 파일 (9)

| 파일 | 용도 |
|------|------|
| `src/pages/Marketing.jsx` | 마케팅 분석 페이지 |
| `src/pages/Operations.jsx` | 운영 관리 페이지 |
| `src/pages/Market.jsx` | 시장 분석 페이지 |
| `src/fixtures/marketingStates.js` | 마케팅 Mock 데이터 |
| `src/fixtures/operationsStates.js` | 운영 Mock 데이터 |
| `src/fixtures/marketStates.js` | 시장 분석 Mock 데이터 |
| `src/components/RiskGauge.jsx` | 위험도 게이지 (폐강 위험 + 포화도) |
| `src/components/ScoreBar.jsx` | 점수 바 (composite_score 표시) |
| `src/components/FieldSelector.jsx` | 분야 선택 드롭다운 (공통) |

### 수정 파일 (4)

| 파일 | 변경 |
|------|------|
| `src/App.jsx` | 3개 라우트 추가 (/marketing, /operations, /market) |
| `src/components/Layout.jsx` | 사이드바에 3개 네비게이션 링크 추가 |
| `src/api/adapters/mockAdapter.js` | 6개 Mock 함수 추가 |
| `src/api/adapters/index.js` | 6개 함수 export 추가 |

---

## 구현 순서

1. **인프라:** FieldSelector, RiskGauge, ScoreBar 공통 컴포넌트
2. **fixtures:** marketingStates, operationsStates, marketStates Mock 데이터
3. **mockAdapter + index:** 6개 Mock 함수 추가
4. **페이지:** Marketing.jsx → Operations.jsx → Market.jsx
5. **라우팅:** App.jsx 라우트 + Layout.jsx 사이드바 네비 추가
6. **검증:** 브라우저에서 각 페이지 렌더링 확인

---

## 검증 계획

1. `npm run dev` 후 각 페이지 URL 접근 확인
2. 분야 선택 변경 시 데이터 갱신 확인
3. 폼 입력 → 결과 표시 흐름 확인 (운영 관리)
4. 반응형 레이아웃 확인 (카드 그리드 리사이즈)
5. 기존 Dashboard, Simulator 동작 불변 확인
