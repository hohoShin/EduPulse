import { createUIState, createSummaryCard, createChartPoint, createAlertItem } from '../api/viewModels.js';

export const dashboardSummarySuccess = createUIState({
  state: 'success',
  isDemo: true,
  data: [
    createSummaryCard('total-enrollment', '총 수강생', 1250, '명', 12.5, '지난 학기 대비', 'up', 'users'),
    createSummaryCard('active-courses', '진행 중인 강좌', 42, '개', 2, '지난 학기 대비', 'up', 'book-open'),
    createSummaryCard('demand-index', '시장 수요 지수', 'High', '', 5, '지난달 대비', 'up', 'trending-up'),
  ],
});

export const dashboardSummaryLoading = createUIState({ state: 'loading', isDemo: true });
export const dashboardSummaryEmpty = createUIState({ state: 'empty', isDemo: true });
export const dashboardSummaryError = createUIState({
  state: 'error',
  isDemo: true,
  error: '대시보드 요약을 가져오지 못했습니다.',
});

export const demandChartSuccess = createUIState({
  state: 'success',
  isDemo: true,
  data: [
    createChartPoint('2026-01-01', 450, 480, 420),
    createChartPoint('2026-02-01', 480, 510, 450),
    createChartPoint('2026-03-01', 520, 550, 490),
    createChartPoint('2026-04-01', 600, 640, 560),
  ],
});

export const demandChartLoading = createUIState({ state: 'loading', isDemo: true });
export const demandChartEmpty = createUIState({ state: 'empty', isDemo: true });
export const demandChartError = createUIState({
  state: 'error',
  isDemo: true,
  error: '수요 차트 데이터를 불러오지 못했습니다.',
});

export const dashboardAlertsSuccess = createUIState({
  state: 'success',
  isDemo: true,
  data: [
    createAlertItem('alert-1', '폐강 위험 감지', '고급 게임 디자인(5월 기수)의 목표 등록률이 40%입니다.', 'critical', '2026-04-09T10:00:00Z', '가격 조정'),
    createAlertItem('alert-2', '광고 적기 임박', '사이버 보안 부트캠프 검색 트렌드가 정점에 달했습니다. 지금 광고를 시작하세요.', 'warning', '2026-04-09T09:30:00Z', '마케팅 계획 보기'),
  ],
});

export const dashboardAlertsLoading = createUIState({ state: 'loading', isDemo: true });
export const dashboardAlertsEmpty = createUIState({ state: 'empty', isDemo: true });
export const dashboardAlertsError = createUIState({
  state: 'error',
  isDemo: true,
  error: '시스템 알림을 검색하지 못했습니다.',
});
