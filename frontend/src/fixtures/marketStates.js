import { createUIState } from '../api/viewModels.js';

export const demographicsData = {
  coding: {
    field: "coding",
    total_students: 200,
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
  security: { field: "security", total_students: 120, age_distribution: [{group:"20대",ratio:0.45},{group:"30대",ratio:0.40},{group:"40대 이상",ratio:0.15}], purpose_distribution: [{purpose:"취업",ratio:0.48},{purpose:"취미",ratio:0.12},{purpose:"자격증",ratio:0.40}], trend: "안정" },
  game: { field: "game", total_students: 180, age_distribution: [{group:"20대",ratio:0.65},{group:"30대",ratio:0.25},{group:"40대 이상",ratio:0.10}], purpose_distribution: [{purpose:"취업",ratio:0.50},{purpose:"취미",ratio:0.35},{purpose:"자격증",ratio:0.15}], trend: "증가" },
  art: { field: "art", total_students: 150, age_distribution: [{group:"20대",ratio:0.50},{group:"30대",ratio:0.30},{group:"40대 이상",ratio:0.20}], purpose_distribution: [{purpose:"취업",ratio:0.35},{purpose:"취미",ratio:0.45},{purpose:"자격증",ratio:0.20}], trend: "안정" },
};

export const competitorsData = {
  coding: { field: "coding", competitor_openings: 8, previous_openings: 6, competitor_avg_price: 1200000, previous_avg_price: 1100000, saturation_index: 1.2, recommendation: "경쟁이 활발합니다. 가격 경쟁력 또는 강사 전문성 강화를 권장합니다." },
  security: { field: "security", competitor_openings: 3, previous_openings: 4, competitor_avg_price: 1500000, previous_avg_price: 1450000, saturation_index: 0.6, recommendation: "시장 여유가 있습니다. 전문성 특화 전략으로 선점 효과를 노리세요." },
  game: { field: "game", competitor_openings: 5, previous_openings: 5, competitor_avg_price: 1100000, previous_avg_price: 1050000, saturation_index: 0.9, recommendation: "적정 경쟁 수준입니다. 포트폴리오 중심의 차별화를 추천합니다." },
  art: { field: "art", competitor_openings: 4, previous_openings: 5, competitor_avg_price: 900000, previous_avg_price: 950000, saturation_index: 0.7, recommendation: "시장 포화도가 낮습니다. 신규 강좌 개설에 유리한 환경입니다." },
};

export const optimalStartData = {
  coding: {
    top_candidates: [
      { date: "2026-07-06", predicted_enrollment: 7, demand_tier: "High", composite_score: 85, competitor_count: 3, search_trend: "상승" },
      { date: "2026-07-13", predicted_enrollment: 6, demand_tier: "High", composite_score: 78, competitor_count: 4, search_trend: "상승" },
      { date: "2026-06-29", predicted_enrollment: 5, demand_tier: "Mid", composite_score: 65, competitor_count: 3, search_trend: "안정" },
      { date: "2026-07-20", predicted_enrollment: 5, demand_tier: "Mid", composite_score: 60, competitor_count: 5, search_trend: "안정" },
      { date: "2026-06-22", predicted_enrollment: 4, demand_tier: "Mid", composite_score: 52, competitor_count: 4, search_trend: "하락" },
    ]
  },
  security: {
    top_candidates: [
      { date: "2026-08-03", predicted_enrollment: 5, demand_tier: "Mid", composite_score: 72, competitor_count: 2, search_trend: "상승" },
      { date: "2026-07-27", predicted_enrollment: 4, demand_tier: "Mid", composite_score: 65, competitor_count: 2, search_trend: "안정" },
      { date: "2026-08-10", predicted_enrollment: 4, demand_tier: "Mid", composite_score: 58, competitor_count: 3, search_trend: "안정" },
      { date: "2026-07-20", predicted_enrollment: 3, demand_tier: "Low", composite_score: 45, competitor_count: 3, search_trend: "하락" },
      { date: "2026-08-17", predicted_enrollment: 3, demand_tier: "Low", composite_score: 40, competitor_count: 4, search_trend: "하락" },
    ]
  },
  game: {
    top_candidates: [
      { date: "2026-07-06", predicted_enrollment: 6, demand_tier: "High", composite_score: 80, competitor_count: 2, search_trend: "상승" },
      { date: "2026-07-13", predicted_enrollment: 5, demand_tier: "Mid", composite_score: 70, competitor_count: 3, search_trend: "상승" },
      { date: "2026-06-29", predicted_enrollment: 5, demand_tier: "Mid", composite_score: 62, competitor_count: 3, search_trend: "안정" },
      { date: "2026-07-20", predicted_enrollment: 4, demand_tier: "Mid", composite_score: 55, competitor_count: 4, search_trend: "안정" },
      { date: "2026-06-22", predicted_enrollment: 3, demand_tier: "Low", composite_score: 42, competitor_count: 5, search_trend: "하락" },
    ]
  },
  art: {
    top_candidates: [
      { date: "2026-09-07", predicted_enrollment: 4, demand_tier: "Mid", composite_score: 68, competitor_count: 2, search_trend: "상승" },
      { date: "2026-09-14", predicted_enrollment: 4, demand_tier: "Mid", composite_score: 62, competitor_count: 2, search_trend: "안정" },
      { date: "2026-08-31", predicted_enrollment: 3, demand_tier: "Low", composite_score: 50, competitor_count: 3, search_trend: "안정" },
      { date: "2026-09-21", predicted_enrollment: 3, demand_tier: "Low", composite_score: 45, competitor_count: 3, search_trend: "하락" },
      { date: "2026-08-24", predicted_enrollment: 2, demand_tier: "Low", composite_score: 35, competitor_count: 4, search_trend: "하락" },
    ]
  },
};

export const demographicsSuccess = (field) => createUIState({ state: 'success', isDemo: true, data: demographicsData[field] || demographicsData.coding });
export const competitorsSuccess = (field) => createUIState({ state: 'success', isDemo: true, data: competitorsData[field] || competitorsData.coding });
export const optimalStartSuccess = (field) => createUIState({ state: 'success', isDemo: true, data: optimalStartData[field] || optimalStartData.coding });
