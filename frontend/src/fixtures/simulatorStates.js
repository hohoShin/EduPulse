import { createUIState, createSimulatorResult } from '../api/viewModels.js';

export const simulatorResultSuccess = createUIState({
  state: 'success',
  isDemo: true,
  data: createSimulatorResult({
    courseName: '풀스택 AI 웹 개발',
    field: 'coding',
    predictedCount: 85,
    demandTier: 'High',
    confidenceInterval: {
      lower: 78,
      upper: 92,
    },
    modelUsed: 'Ensemble (XGBoost + Prophet)',
    predictionDate: '2026-04-09T14:00:00Z',
    marketing: {
      adWeeksBefore: 4,
      earlybirdDays: 14,
      discountRate: 0.15,
    },
    operations: {
      instructors: 3,
      classrooms: 2,
    },
  }),
});

export const simulatorLoading = createUIState({ state: 'loading', isDemo: true });
export const simulatorEmpty = createUIState({ state: 'empty', isDemo: true });
export const simulatorError = createUIState({
  state: 'error',
  isDemo: true,
  error: '시뮬레이션을 실행하지 못했습니다. 외부 트렌드 연결 상태를 확인해주세요.',
});
