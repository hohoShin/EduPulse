import { createUIState, createStatusItem } from '../api/viewModels.js';

export const systemStatusSuccess = createUIState({
  state: 'success',
  isDemo: true,
  data: [
    createStatusItem('수요 예측 엔진', 'ok', '2026-04-09T13:45:00Z', { cpu: 12, memory: 450 }),
    createStatusItem('네이버 데이터랩 API', 'ok', '2026-04-09T14:00:00Z', { apiQuotaUsed: 420, apiQuotaLimit: 1000 }),
    createStatusItem('구글 트렌드 크롤러', 'degraded', '2026-04-09T12:00:00Z', { cpu: 85, memory: 1200 }),
  ],
});

export const systemStatusLoading = createUIState({ state: 'loading', isDemo: true });
export const systemStatusEmpty = createUIState({ state: 'empty', isDemo: true });
export const systemStatusError = createUIState({
  state: 'error',
  isDemo: true,
  error: '시스템 상태 지표를 가져오지 못했습니다.',
});
