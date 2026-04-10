import { createUIState } from '../api/viewModels.js';

export const demographicsData = {
  coding: {
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
  },
  security: { field: "security", age_distribution: [{group:"20대",ratio:0.45},{group:"30대",ratio:0.40},{group:"40대 이상",ratio:0.15}], purpose_distribution: [{purpose:"취업",ratio:0.48},{purpose:"취미",ratio:0.12},{purpose:"자격증",ratio:0.40}], trend: "안정" },
  game: { field: "game", age_distribution: [{group:"20대",ratio:0.65},{group:"30대",ratio:0.25},{group:"40대 이상",ratio:0.10}], purpose_distribution: [{purpose:"취업",ratio:0.50},{purpose:"취미",ratio:0.35},{purpose:"자격증",ratio:0.15}], trend: "증가" },
  art: { field: "art", age_distribution: [{group:"20대",ratio:0.50},{group:"30대",ratio:0.30},{group:"40대 이상",ratio:0.20}], purpose_distribution: [{purpose:"취업",ratio:0.35},{purpose:"취미",ratio:0.45},{purpose:"자격증",ratio:0.20}], trend: "안정" },
};

export const competitorsData = {
  coding: { field: "coding", competitor_openings: 8, competitor_avg_price: 1200000, saturation_index: 1.2, recommendation: "경쟁이 활발합니다. 가격 경쟁력 또는 강사 전문성 강화를 권장합니다." },
  security: { field: "security", competitor_openings: 3, competitor_avg_price: 1500000, saturation_index: 0.6, recommendation: "시장 여유가 있습니다. 전문성 특화 전략으로 선점 효과를 노리세요." },
  game: { field: "game", competitor_openings: 5, competitor_avg_price: 1100000, saturation_index: 0.9, recommendation: "적정 경쟁 수준입니다. 포트폴리오 중심의 차별화를 추천합니다." },
  art: { field: "art", competitor_openings: 4, competitor_avg_price: 900000, saturation_index: 0.7, recommendation: "시장 포화도가 낮습니다. 신규 강좌 개설에 유리한 환경입니다." },
};

export const optimalStartData = {
  coding: {
    top_candidates: [
      { date: "2026-07-06", predicted_enrollment: 7, demand_tier: "High", composite_score: 0.85 },
      { date: "2026-07-13", predicted_enrollment: 6, demand_tier: "High", composite_score: 0.78 },
      { date: "2026-06-29", predicted_enrollment: 5, demand_tier: "Mid", composite_score: 0.65 },
      { date: "2026-07-20", predicted_enrollment: 5, demand_tier: "Mid", composite_score: 0.60 },
      { date: "2026-06-22", predicted_enrollment: 4, demand_tier: "Mid", composite_score: 0.52 },
    ]
  },
  security: {
    top_candidates: [
      { date: "2026-08-03", predicted_enrollment: 5, demand_tier: "Mid", composite_score: 0.72 },
      { date: "2026-07-27", predicted_enrollment: 4, demand_tier: "Mid", composite_score: 0.65 },
      { date: "2026-08-10", predicted_enrollment: 4, demand_tier: "Mid", composite_score: 0.58 },
      { date: "2026-07-20", predicted_enrollment: 3, demand_tier: "Low", composite_score: 0.45 },
      { date: "2026-08-17", predicted_enrollment: 3, demand_tier: "Low", composite_score: 0.40 },
    ]
  },
  game: {
    top_candidates: [
      { date: "2026-07-06", predicted_enrollment: 6, demand_tier: "High", composite_score: 0.80 },
      { date: "2026-07-13", predicted_enrollment: 5, demand_tier: "Mid", composite_score: 0.70 },
      { date: "2026-06-29", predicted_enrollment: 5, demand_tier: "Mid", composite_score: 0.62 },
      { date: "2026-07-20", predicted_enrollment: 4, demand_tier: "Mid", composite_score: 0.55 },
      { date: "2026-06-22", predicted_enrollment: 3, demand_tier: "Low", composite_score: 0.42 },
    ]
  },
  art: {
    top_candidates: [
      { date: "2026-09-07", predicted_enrollment: 4, demand_tier: "Mid", composite_score: 0.68 },
      { date: "2026-09-14", predicted_enrollment: 4, demand_tier: "Mid", composite_score: 0.62 },
      { date: "2026-08-31", predicted_enrollment: 3, demand_tier: "Low", composite_score: 0.50 },
      { date: "2026-09-21", predicted_enrollment: 3, demand_tier: "Low", composite_score: 0.45 },
      { date: "2026-08-24", predicted_enrollment: 2, demand_tier: "Low", composite_score: 0.35 },
    ]
  },
};

export const demographicsSuccess = (field) => createUIState({ state: 'success', isDemo: true, data: demographicsData[field] || demographicsData.coding });
export const competitorsSuccess = (field) => createUIState({ state: 'success', isDemo: true, data: competitorsData[field] || competitorsData.coding });
export const optimalStartSuccess = (field) => createUIState({ state: 'success', isDemo: true, data: optimalStartData[field] || optimalStartData.coding });
