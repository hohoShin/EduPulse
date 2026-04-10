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

/**
 * 시나리오 비교 데이터 — 기본/낙관/비관 3가지 시나리오를 제공합니다.
 * Simulator 페이지의 시나리오 카드에서 사용됩니다.
 */
export const scenarioBaseline = {
  scenario: 'baseline',
  label: '기본 시나리오',
  description: '현재 시장 트렌드와 과거 평균을 기반으로 한 예측',
  predictedCount: 85,
  demandTier: 'High',
  confidenceInterval: { lower: 78, upper: 92 },
  marketing: { adWeeksBefore: 4, earlybirdDays: 14, discountRate: 0.15 },
  operations: { instructors: 3, classrooms: 2 },
};

export const scenarioOptimistic = {
  scenario: 'optimistic',
  label: '낙관 시나리오',
  description: '검색 트렌드 상승 및 경쟁 강좌 감소를 가정한 예측',
  predictedCount: 112,
  demandTier: 'High',
  confidenceInterval: { lower: 98, upper: 126 },
  marketing: { adWeeksBefore: 3, earlybirdDays: 10, discountRate: 0.10 },
  operations: { instructors: 4, classrooms: 3 },
};

export const scenarioPessimistic = {
  scenario: 'pessimistic',
  label: '비관 시나리오',
  description: '비수기 및 유사 강좌 증가를 가정한 예측',
  predictedCount: 42,
  demandTier: 'Mid',
  confidenceInterval: { lower: 35, upper: 50 },
  marketing: { adWeeksBefore: 6, earlybirdDays: 21, discountRate: 0.25 },
  operations: { instructors: 2, classrooms: 1 },
};
