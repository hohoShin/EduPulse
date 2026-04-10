# 프론트엔드 5페이지 고도화 구현 계획

**Date:** 2026-04-10
**Branch:** `feat/frontend-enhancement-v2` (from `dev`)
**Phase:** A (Mock 데이터 기반, 백엔드 연동 없음)

---

## 요약

기존 5개 프론트엔드 페이지의 UX/기능을 고도화한다.
기존 패턴(Mock adapter, CSS 변수, Recharts, useState/useEffect) 준수.
새 API 호출 없음 — fixture 데이터 확장 + 프론트 로직으로 구현.

---

## 페이지별 개선 사항

### 1. Dashboard (`/`) — `Dashboard.jsx`

| # | 개선 | 현재 | 변경 |
|---|------|------|------|
| D1 | 분야 필터 추가 | 전체 합산만 표시 | FieldSelector 추가, 분야별 요약 카드·차트·알림 분리 |
| D2 | 수요 예측 차트 고도화 | 단일 LineChart 4포인트 | 분야별 멀티라인 + 신뢰 구간(Area) + 8주 데이터 |

**변경 파일:**
- `frontend/src/pages/Dashboard.jsx` — FieldSelector import, field state, 분야별 데이터 필터링
- `frontend/src/fixtures/dashboardStates.js` — 분야별 데이터 구조 확장 (coding/security/game/art 각각)
- `frontend/src/api/adapters/mockAdapter.js` — `getDashboardSummary`, `getDemandChart`에 field 파라미터 지원

**D1 상세:**
- FieldSelector를 데모 스위처 아래에 배치
- `getDashboardSummary({ field, forceState })` → field별 다른 수치 반환
- `getDemandChart({ field, forceState })` → field별 차트 데이터 반환
- `getDashboardAlerts({ field, forceState })` → field별 알림 필터

**D2 상세:**
- demandChartSuccess → 8주 데이터 (현재 4주)
- chartPoint에 upper/lower 이미 있음 → Area 영역으로 신뢰 구간 시각화
- DemandChart 컴포넌트에 ComposedChart(Line + Area) 패턴 적용

---

### 2. Simulator (`/simulator`) — `Simulator.jsx`

| # | 개선 | 현재 | 변경 |
|---|------|------|------|
| S1 | 시나리오 비교 | 단일 예측값만 | baseline/optimistic/pessimistic 3개 시나리오 카드 |
| S2 | 수강료 입력 | 폼에 없음 | 수강료 입력 필드 추가 → 가격 수준별 수요 변화 표시 |
| S3 | 결과 재실행 편의 | 결과 나와도 폼 변경 어려움 | "조건 변경" 버튼 + 결과 영역에 입력값 요약 표시 |

**변경 파일:**
- `frontend/src/pages/Simulator.jsx` — 시나리오 비교 UI, 수강료 입력, 조건 변경 버튼
- `frontend/src/fixtures/simulatorStates.js` — optimistic/pessimistic 시나리오 데이터 추가
- `frontend/src/api/adapters/mockAdapter.js` — `simulateDemand` 응답에 시나리오 데이터 포함

**S1 상세:**
- fixture에 `scenarios: { baseline, optimistic, pessimistic }` 추가
- baseline = 현재 predictedCount, optimistic = baseline * 1.2, pessimistic = baseline * 0.8
- 3개 카드를 나란히 배치, 각각 예측 인원 + 수요 등급 + 신뢰 구간
- baseline 카드에 "기본" 배지, optimistic에 "낙관", pessimistic에 "보수"

**S2 상세:**
- 폼에 `tuitionFee` 숫자 입력 (만원 단위, placeholder: "예: 120")
- Mock: 수강료 100만원 이하 → 수요 +10%, 150만원 이상 → 수요 -10%
- 결과 카드에 "수강료 기준 보정" 라벨 표시

**S3 상세:**
- 결과 영역 상단에 입력 요약 표시 (강좌명, 분야, 날짜, 수강료)
- "조건 변경" 버튼 → `setUiState({ state: 'empty' })` + 폼에 포커스
- 결과 카드 하단에 "다시 실행" 버튼 → 현재 폼값으로 재실행

---

### 3. Marketing (`/marketing`) — `Marketing.jsx`

| # | 개선 | 현재 | 변경 |
|---|------|------|------|
| M1 | 전환율 변화율 표시 | 숫자만 표시 | 이전 기간 대비 +/- % 표시 |
| M2 | 차트 목표선 | 단순 LineChart | ReferenceLine으로 목표 전환율 기준선 |
| M3 | 타이밍 카드 동적 강조 | 3개 카드 동일 스타일 | 현재 분야 수요 등급에 해당하는 카드 강조, 나머지 dimmed |
| M4 | 추천 사항 액션 링크 | 텍스트만 | 추천별 관련 페이지 링크 버튼 |

**변경 파일:**
- `frontend/src/pages/Marketing.jsx` — 변화율 계산, ReferenceLine, 카드 강조, 액션 링크
- `frontend/src/fixtures/marketingStates.js` — `previous_conversions`, `target_conversion_rate`, `current_demand_tier` 추가

**M1 상세:**
- fixture에 `previous_conversions` 추가 (이전 기간 전환 수)
- 전환 수 카드에 `((current - previous) / previous * 100).toFixed(1)%` 표시
- 양수면 trend-up 스타일, 음수면 trend-down

**M2 상세:**
- fixture에 `target_conversion_rate: 0.35` 추가
- LineChart에 `<ReferenceLine y={35} stroke="#DC2626" strokeDasharray="5 5" label="목표" />`
- Recharts ReferenceLine import 추가

**M3 상세:**
- fixture에 `current_demand_tier: "High"` 추가 (분야별)
- 타이밍 카드 렌더링 시 `item.demand_tier === currentDemandTier` 이면 기존 스타일, 아니면 opacity: 0.5 + grayscale
- 강조 카드에 "현재 등급" 배지

**M4 상세:**
- recommendations 배열을 `{ text, link }` 객체로 확장
- link 값: "/simulator" (시뮬레이션), "/operations" (운영), "/market" (시장)
- `<Link to={link}>` 버튼 추가 (react-router-dom NavLink)

---

### 4. Operations (`/operations`) — `Operations.jsx`

| # | 개선 | 현재 | 변경 |
|---|------|------|------|
| O1 | 위험도 추세 표시 | 게이지만 | 최근 4주 위험도 변화 미니 차트 추가 |
| O2 | 배정 테이블 편집 | 읽기 전용 | 시간대 변경 드롭다운 (목업 수준 인터랙션) |
| O3 | 폐강↔마케팅 연계 | 별도 액션 없음 | 위험도 high 시 "마케팅 강화" 버튼 → /marketing 링크 |
| O4 | 예상 수강생 수 표시 | 없음 | 예상 등록 인원 + 최소 개강 인원 비교 카드 |

**변경 파일:**
- `frontend/src/pages/Operations.jsx` — 미니 차트, 편집 UI, 링크 버튼, 수강생 카드
- `frontend/src/fixtures/operationsStates.js` — `risk_trend`, `predicted_enrollment`, `min_enrollment` 추가
- `frontend/src/api/adapters/mockAdapter.js` — `getClosureRisk` 응답 확장

**O1 상세:**
- fixture에 `risk_trend: [0.45, 0.55, 0.62, 0.72]` (최근 4주)
- Recharts 미니 LineChart (높이 60px, 축 없음, 도트만)

**O2 상세:**
- 배정 테이블의 time_slot 셀을 `<select>`로 교체
- 옵션: "오전 (09:00-12:00)", "오후 (13:00-16:00)", "저녁 (18:00-21:00)"
- 변경 시 `useState`로 로컬 상태만 업데이트 (Mock이므로 서버 반영 없음)
- 테이블 하단에 "변경사항은 데모 모드에서 저장되지 않습니다" 안내

**O3 상세:**
- `riskData.risk_level === 'high'` 일 때 추천 카드 아래에 액션 버튼 그룹
- "마케팅 분석 바로가기" → `<Link to="/marketing">`
- "시뮬레이터에서 재분석" → `<Link to="/simulator">`

**O4 상세:**
- fixture에 `predicted_enrollment: 3`, `min_enrollment: 5` 추가
- 폐강 위험도 섹션 상단에 2컬럼 카드: 예상 인원 vs 최소 인원
- 미달이면 차이를 빨간색으로 강조 ("2명 부족")

---

### 5. Market (`/market`) — `Market.jsx`

| # | 개선 | 현재 | 변경 |
|---|------|------|------|
| K1 | 파이차트 범례 추가 | label만 | Recharts Legend + 호버 시 인원수 |
| K2 | 경쟁사 증감 트렌드 | 숫자만 | 이전 기간 대비 +/- 표시 |
| K3 | 최적 개강일 날짜 범위 | 분야만 선택 | start/end date 입력 |
| K4 | 포화도 게이지 라벨 | RiskGauge 재사용 (위험도 라벨) | 포화도 전용 라벨 ("여유/보통/포화") |
| K5 | 후보 카드 부가 정보 | 날짜+인원+점수만 | 해당 주 경쟁 개강 수 + 검색 트렌드 표시 |

**변경 파일:**
- `frontend/src/pages/Market.jsx` — Legend, 트렌드 표시, 날짜 범위, 라벨 전달, 카드 확장
- `frontend/src/fixtures/marketStates.js` — `previous_openings`, `previous_avg_price`, 후보별 `competitor_count`, `search_trend` 추가
- `frontend/src/components/RiskGauge.jsx` — `labels` prop 지원 (커스텀 라벨)

**K1 상세:**
- PieChart에 `<Legend />` 추가
- Tooltip에 `formatter: (v) => [(v * totalStudents).toFixed(0) + '명', '추정 인원']`
- fixture에 `total_students: 200` (추정 전체 수강생) 추가

**K2 상세:**
- fixture에 `previous_openings`, `previous_avg_price` 추가
- 경쟁사 카드에 변화량 표시: "+2개 ↑" (초록) 또는 "-1개 ↓" (빨강)

**K3 상세:**
- FieldSelector 옆에 시작일/종료일 date input 2개
- Mock: 날짜 범위와 무관하게 동일 데이터 반환 (UI만 구현)
- getOptimalStart에 `{ field, startDate, endDate }` 파라미터 전달

**K4 상세:**
- RiskGauge에 `labels` prop 추가: `{ high: '포화', medium: '보통', low: '여유' }`
- 기존 기본값 유지: `{ high: '위험', medium: '주의', low: '안전' }`
- Market 페이지에서 포화도 게이지 호출 시 `labels={{ high: '포화', medium: '보통', low: '여유' }}` 전달

**K5 상세:**
- fixture candidates에 `competitor_count: 3`, `search_trend: "상승"` 추가
- 후보 카드 하단에 "경쟁 3개 | 검색 상승" 라벨

---

### 6. 공통 개선

| # | 개선 | 현재 | 변경 |
|---|------|------|------|
| C1 | 페이지 간 네비게이션 | 없음 | 결과 카드에 관련 페이지 바로가기 링크 |
| C2 | 에러 핸들링 통일 | Dashboard만 완전, 나머지 불균일 | Marketing, Market에 에러 state 처리 추가 |
| C3 | 데이터 새로고침 | 없음 | 각 페이지에 새로고침 버튼 |

**C1 상세:**
- Simulator 결과 → "운영 관리에서 상세 분석" 링크 (이미 O3에서 역방향 처리)
- Dashboard 알림 → actionUrl 필드 활용하여 `<Link>` 연결
- 공통 `PageLink` 컴포넌트는 만들지 않음 (인라인 `<Link>`)

**C2 상세:**
- Marketing.jsx: `fetchData`에 try/catch 추가, error state 처리
- Market.jsx: `fetchData`에 try/catch 추가, error state 처리
- 에러 시 StatusPanel variant="error" 표시

**C3 상세:**
- 각 페이지 헤더 우측에 새로고침 버튼 (SVG 아이콘)
- 클릭 시 해당 페이지의 fetch 함수 재호출
- Dashboard: demoState 유지하고 refetch
- Marketing/Market: field 유지하고 refetch
- Operations/Simulator: 결과 초기화 (폼 재제출 필요)

---

## 파일 변경 목록

### 수정 파일 (10)

| 파일 | 변경 |
|------|------|
| `frontend/src/pages/Dashboard.jsx` | D1(FieldSelector), D2(차트 고도화), C3(새로고침) |
| `frontend/src/pages/Simulator.jsx` | S1(시나리오), S2(수강료), S3(재실행), C1(링크) |
| `frontend/src/pages/Marketing.jsx` | M1(변화율), M2(목표선), M3(강조), M4(액션), C2(에러), C3(새로고침) |
| `frontend/src/pages/Operations.jsx` | O1(추세), O2(편집), O3(연계), O4(수강생), C3(새로고침) |
| `frontend/src/pages/Market.jsx` | K1(범례), K2(증감), K3(날짜), K4(라벨), K5(부가정보), C2(에러), C3(새로고침) |
| `frontend/src/fixtures/dashboardStates.js` | D1(분야별 데이터), D2(8주 데이터+Area) |
| `frontend/src/fixtures/simulatorStates.js` | S1(시나리오 데이터), S2(수강료 보정) |
| `frontend/src/fixtures/marketingStates.js` | M1(previous), M2(target), M3(current_tier), M4(추천 링크) |
| `frontend/src/fixtures/operationsStates.js` | O1(risk_trend), O4(enrollment 데이터) |
| `frontend/src/fixtures/marketStates.js` | K2(previous), K5(부가정보) |
| `frontend/src/api/adapters/mockAdapter.js` | D1(field 파라미터), 확장된 fixture 연결 |
| `frontend/src/components/RiskGauge.jsx` | K4(labels prop) |

### 신규 파일: 없음

---

## 구현 순서

### Phase 1: 공통 인프라 (C2, C3, K4)
1. `RiskGauge.jsx` — labels prop 추가 (K4)
2. Marketing.jsx, Market.jsx — try/catch 에러 핸들링 (C2)
3. 5개 페이지 — 새로고침 버튼 (C3)

### Phase 2: Fixtures 확장
4. `dashboardStates.js` — 분야별 데이터 + 8주 차트 (D1, D2)
5. `simulatorStates.js` — 시나리오 3종 데이터 (S1, S2)
6. `marketingStates.js` — previous_conversions, target_rate, current_tier, 추천 링크 (M1~M4)
7. `operationsStates.js` — risk_trend, predicted/min enrollment (O1, O4)
8. `marketStates.js` — previous 데이터, 후보 부가정보 (K2, K5)

### Phase 3: MockAdapter 확장
9. `mockAdapter.js` — field 파라미터 지원, 확장된 fixture 연결

### Phase 4: 페이지 UI (의존성 순)
10. `Dashboard.jsx` — FieldSelector + 분야별 필터 + Area 차트 (D1, D2)
11. `Simulator.jsx` — 시나리오 카드 + 수강료 입력 + 재실행 (S1, S2, S3)
12. `Marketing.jsx` — 변화율 + 목표선 + 강조 + 액션 링크 (M1~M4)
13. `Operations.jsx` — 미니 차트 + 편집 + 연계 + 수강생 (O1~O4)
14. `Market.jsx` — 범례 + 증감 + 날짜범위 + 부가정보 (K1~K5)
15. 페이지 간 네비게이션 링크 (C1)

### Phase 5: 검증
16. `npx vite build` 빌드 확인
17. 브라우저 수동 확인 (5페이지 각각)

---

## 검증 계획

1. `npx vite build` — 빌드 에러 0건
2. 각 페이지 URL 직접 접근 → 렌더링 확인
3. Dashboard: 분야 선택 변경 시 카드/차트/알림 갱신 확인
4. Simulator: 시나리오 3개 카드 표시 + 수강료 입력 반영 확인
5. Marketing: 목표선 표시 + 강조 카드 + 액션 링크 동작 확인
6. Operations: 미니 차트 + 드롭다운 변경 + 마케팅 링크 확인
7. Market: 범례 + 증감 + 날짜 입력 + 포화도 라벨 확인
8. 에러 핸들링: 콘솔 에러 0건
9. 기존 기능 회귀 없음 (각 페이지 기본 흐름 정상)

---

## 수정 규모 예상

- 수정 파일: 12개
- 신규 파일: 0개
- 주요 변경: fixture 데이터 확장 + 페이지 UI 추가
- 리스크: 낮음 (기존 구조 유지, Mock 전용, 백엔드 의존 없음)
