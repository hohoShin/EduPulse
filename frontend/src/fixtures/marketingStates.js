import { createUIState } from '../api/viewModels.js';

export const leadConversionData = {
  coding: {
    field: "coding",
    estimated_conversions: 42,
    previous_conversions: 38,
    current_demand_tier: "High",
    consultation_count_trend: [120, 115, 130, 125, 140, 135, 150, 145],
    recommendations: [
      { text: "상담 문의가 증가하고 있습니다. 상담 인력 확충 또는 자동 응답 시스템 도입을 검토하세요.", link: "/operations" },
      { text: "상담 후 미등록 고객에 대한 후속 연락을 강화하세요.", link: "/operations" },
      { text: "취업/이직 시즌(1~2월, 7~8월) 집중 광고를 권장합니다.", link: "/marketing" },
    ]
  },
  security: {
    field: "security",
    estimated_conversions: 28,
    previous_conversions: 24,
    current_demand_tier: "Mid",
    consultation_count_trend: [80,85,78,90,88,95,92,100],
    recommendations: [
      { text: "상담 문의가 증가하고 있습니다. 상담 인력 확충 또는 자동 응답 시스템 도입을 검토하세요.", link: "/operations" },
      { text: "자격증 시험 일정에 맞춰 3~4주 전 집중 마케팅을 실시하세요.", link: "/marketing" },
      { text: "기업 교육 연계 프로그램을 홍보하세요.", link: "/market" },
    ]
  },
  game: {
    field: "game",
    estimated_conversions: 35,
    previous_conversions: 31,
    current_demand_tier: "Mid",
    consultation_count_trend: [95,100,92,105,98,110,108,115],
    recommendations: [
      { text: "상담 문의가 증가하고 있습니다. 상담 인력 확충 또는 자동 응답 시스템 도입을 검토하세요.", link: "/operations" },
      { text: "게임쇼/콘퍼런스 시즌과 연계한 이벤트 마케팅을 고려하세요.", link: "/market" },
      { text: "방학 시즌 집중 과정을 준비하세요.", link: "/operations" },
    ]
  },
  art: {
    field: "art",
    estimated_conversions: 22,
    previous_conversions: 25,
    current_demand_tier: "Low",
    consultation_count_trend: [65,70,68,75,72,78,80,82],
    recommendations: [
      { text: "상담 문의가 증가하고 있습니다. 상담 인력 확충 또는 자동 응답 시스템 도입을 검토하세요.", link: "/operations" },
      { text: "포트폴리오 공개 시즌 전후로 마케팅을 강화하세요.", link: "/marketing" },
      { text: "취미반과 전문반을 분리하여 타겟팅하세요.", link: "/operations" },
    ]
  },
};

export const marketingTimingData = {
  coding: [
    { demand_tier: "High", ad_launch_weeks_before: 2, earlybird_duration_days: 7, discount_rate: 0.05 },
    { demand_tier: "Mid", ad_launch_weeks_before: 3, earlybird_duration_days: 14, discount_rate: 0.10 },
    { demand_tier: "Low", ad_launch_weeks_before: 4, earlybird_duration_days: 21, discount_rate: 0.15 },
  ],
  security: [
    { demand_tier: "High", ad_launch_weeks_before: 2, earlybird_duration_days: 10, discount_rate: 0.05 },
    { demand_tier: "Mid", ad_launch_weeks_before: 3, earlybird_duration_days: 14, discount_rate: 0.08 },
    { demand_tier: "Low", ad_launch_weeks_before: 5, earlybird_duration_days: 21, discount_rate: 0.12 },
  ],
  game: [
    { demand_tier: "High", ad_launch_weeks_before: 2, earlybird_duration_days: 7, discount_rate: 0.05 },
    { demand_tier: "Mid", ad_launch_weeks_before: 3, earlybird_duration_days: 14, discount_rate: 0.10 },
    { demand_tier: "Low", ad_launch_weeks_before: 4, earlybird_duration_days: 18, discount_rate: 0.13 },
  ],
  art: [
    { demand_tier: "High", ad_launch_weeks_before: 3, earlybird_duration_days: 10, discount_rate: 0.07 },
    { demand_tier: "Mid", ad_launch_weeks_before: 4, earlybird_duration_days: 14, discount_rate: 0.12 },
    { demand_tier: "Low", ad_launch_weeks_before: 5, earlybird_duration_days: 21, discount_rate: 0.18 },
  ],
};

export const leadConversionSuccess = (field) => createUIState({ state: 'success', isDemo: true, data: leadConversionData[field] || leadConversionData.coding });
export const marketingTimingSuccess = (field) => createUIState({ state: 'success', isDemo: true, data: marketingTimingData[field] || marketingTimingData.coding });
