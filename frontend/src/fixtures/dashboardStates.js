import { createUIState, createSummaryCard, createChartPoint, createAlertItem } from '../api/viewModels.js';

// ---------------------------------------------------------------------------
// Field-specific summary card data
// ---------------------------------------------------------------------------
const summaryDataByField = {
  coding: [
    createSummaryCard('total-enrollment', '총 수강생', 1250, '명', 12.5, '지난 학기 대비', 'up', 'users'),
    createSummaryCard('active-courses', '진행 중인 강좌', 42, '개', 2, '지난 학기 대비', 'up', 'book-open'),
    createSummaryCard('demand-index', '시장 수요 지수', 'High', '', 5, '지난달 대비', 'up', 'trending-up'),
  ],
  security: [
    createSummaryCard('total-enrollment', '총 수강생', 830, '명', 8.2, '지난 학기 대비', 'up', 'users'),
    createSummaryCard('active-courses', '진행 중인 강좌', 27, '개', 1, '지난 학기 대비', 'up', 'book-open'),
    createSummaryCard('demand-index', '시장 수요 지수', 'High', '', 9, '지난달 대비', 'up', 'trending-up'),
  ],
  game: [
    createSummaryCard('total-enrollment', '총 수강생', 640, '명', -3.1, '지난 학기 대비', 'down', 'users'),
    createSummaryCard('active-courses', '진행 중인 강좌', 18, '개', -1, '지난 학기 대비', 'down', 'book-open'),
    createSummaryCard('demand-index', '시장 수요 지수', 'Mid', '', -2, '지난달 대비', 'down', 'trending-up'),
  ],
  art: [
    createSummaryCard('total-enrollment', '총 수강생', 410, '명', 4.7, '지난 학기 대비', 'up', 'users'),
    createSummaryCard('active-courses', '진행 중인 강좌', 14, '개', 0, '지난 학기 대비', 'flat', 'book-open'),
    createSummaryCard('demand-index', '시장 수요 지수', 'Mid', '', 1, '지난달 대비', 'up', 'trending-up'),
  ],
};

// ---------------------------------------------------------------------------
// Field-specific 8-week chart data
// ---------------------------------------------------------------------------
const chartDataByField = {
  coding: [
    createChartPoint('2026-02-16', 390, 420, 360),
    createChartPoint('2026-02-23', 410, 440, 380),
    createChartPoint('2026-03-02', 430, 460, 400),
    createChartPoint('2026-03-09', 460, 495, 425),
    createChartPoint('2026-03-16', 490, 525, 455),
    createChartPoint('2026-03-23', 520, 555, 485),
    createChartPoint('2026-03-30', 565, 605, 525),
    createChartPoint('2026-04-06', 600, 640, 560),
  ],
  security: [
    createChartPoint('2026-02-16', 280, 310, 250),
    createChartPoint('2026-02-23', 295, 325, 265),
    createChartPoint('2026-03-02', 315, 345, 285),
    createChartPoint('2026-03-09', 340, 375, 305),
    createChartPoint('2026-03-16', 370, 405, 335),
    createChartPoint('2026-03-23', 400, 435, 365),
    createChartPoint('2026-03-30', 435, 475, 395),
    createChartPoint('2026-04-06', 470, 510, 430),
  ],
  game: [
    createChartPoint('2026-02-16', 240, 270, 210),
    createChartPoint('2026-02-23', 235, 265, 205),
    createChartPoint('2026-03-02', 228, 258, 198),
    createChartPoint('2026-03-09', 220, 250, 190),
    createChartPoint('2026-03-16', 215, 245, 185),
    createChartPoint('2026-03-23', 210, 240, 180),
    createChartPoint('2026-03-30', 205, 235, 175),
    createChartPoint('2026-04-06', 200, 230, 170),
  ],
  art: [
    createChartPoint('2026-02-16', 140, 165, 115),
    createChartPoint('2026-02-23', 145, 170, 120),
    createChartPoint('2026-03-02', 150, 175, 125),
    createChartPoint('2026-03-09', 155, 180, 130),
    createChartPoint('2026-03-16', 158, 183, 133),
    createChartPoint('2026-03-23', 162, 187, 137),
    createChartPoint('2026-03-30', 167, 192, 142),
    createChartPoint('2026-04-06', 172, 198, 146),
  ],
};

// ---------------------------------------------------------------------------
// Field-specific alerts
// ---------------------------------------------------------------------------
const alertsByField = {
  coding: [],
  security: [],
  game: [
    createAlertItem('closure-1', '폐강 주의', '조기 등록 혜택 제공으로 수강생 확보를 권장합니다. 개강 2주 전 재평가 예정.', 'warning', '2026-04-09T10:00:00Z'),
  ],
  art: [
    createAlertItem('closure-1', '폐강 주의', '조기 등록 혜택 제공으로 수강생 확보를 권장합니다. 개강 2주 전 재평가 예정.', 'warning', '2026-04-09T10:00:00Z'),
  ],
};

// ---------------------------------------------------------------------------
// Field-specific factory functions
// ---------------------------------------------------------------------------
const VALID_FIELDS = ['coding', 'security', 'game', 'art'];

const resolveField = (field) => (VALID_FIELDS.includes(field) ? field : 'coding');

export const dashboardSummaryByField = (field) =>
  createUIState({ state: 'success', isDemo: true, data: summaryDataByField[resolveField(field)] });

export const demandChartByField = (field) =>
  createUIState({ state: 'success', isDemo: true, data: chartDataByField[resolveField(field)] });

export const dashboardAlertsByField = (field) => {
  const alerts = alertsByField[resolveField(field)];
  if (alerts.length === 0) return createUIState({ state: 'empty', isDemo: true });
  return createUIState({ state: 'success', isDemo: true, data: alerts });
};

// ---------------------------------------------------------------------------
// Legacy single-state exports (backward compatible — default to coding)
// ---------------------------------------------------------------------------
export const dashboardSummarySuccess = dashboardSummaryByField('coding');
export const dashboardSummaryLoading = createUIState({ state: 'loading', isDemo: true });
export const dashboardSummaryEmpty = createUIState({ state: 'empty', isDemo: true });
export const dashboardSummaryError = createUIState({
  state: 'error',
  isDemo: true,
  error: '대시보드 요약을 가져오지 못했습니다.',
});

export const demandChartSuccess = demandChartByField('coding');
export const demandChartLoading = createUIState({ state: 'loading', isDemo: true });
export const demandChartEmpty = createUIState({ state: 'empty', isDemo: true });
export const demandChartError = createUIState({
  state: 'error',
  isDemo: true,
  error: '수요 차트 데이터를 불러오지 못했습니다.',
});

export const dashboardAlertsSuccess = dashboardAlertsByField('coding');
export const dashboardAlertsLoading = createUIState({ state: 'loading', isDemo: true });
export const dashboardAlertsEmpty = createUIState({ state: 'empty', isDemo: true });
export const dashboardAlertsError = createUIState({
  state: 'error',
  isDemo: true,
  error: '시스템 알림을 검색하지 못했습니다.',
});
