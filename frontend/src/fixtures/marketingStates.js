import { createUIState } from '../api/viewModels.js';

export const leadConversionData = {
  coding: {
    field: "coding",
    estimated_conversions: 42,
    previous_conversions: 38,
    target_conversion_rate: 0.45,
    current_demand_tier: "High",
    conversion_rate_trend: [0.32, 0.35, 0.33, 0.38, 0.36, 0.40, 0.39, 0.42],
    consultation_count_trend: [120, 115, 130, 125, 140, 135, 150, 145],
    recommendations: [
      { text: "전환율이 상승 추세입니다. 현재 마케팅 전략을 유지하세요.", link: "/marketing" },
      { text: "상담 후 미등록 고객에 대한 후속 연락을 강화하세요.", link: "/operations" },
      { text: "얼리버드 할인으로 조기 등록을 유도하세요.", link: "/simulator" },
    ]
  },
  security: {
    field: "security",
    estimated_conversions: 28,
    previous_conversions: 24,
    target_conversion_rate: 0.35,
    current_demand_tier: "Mid",
    conversion_rate_trend: [0.25,0.27,0.26,0.29,0.28,0.30,0.31,0.33],
    consultation_count_trend: [80,85,78,90,88,95,92,100],
    recommendations: [
      { text: "보안 자격증 시즌에 맞춘 프로모션을 준비하세요.", link: "/marketing" },
      { text: "기업 교육 연계 프로그램을 홍보하세요.", link: "/market" },
      { text: "취업 연계 성공 사례를 마케팅에 활용하세요.", link: "/marketing" },
    ]
  },
  game: {
    field: "game",
    estimated_conversions: 35,
    previous_conversions: 31,
    target_conversion_rate: 0.40,
    current_demand_tier: "Mid",
    conversion_rate_trend: [0.28,0.30,0.29,0.32,0.31,0.34,0.33,0.36],
    consultation_count_trend: [95,100,92,105,98,110,108,115],
    recommendations: [
      { text: "게임 포트폴리오 완성 과정을 강조하세요.", link: "/simulator" },
      { text: "방학 시즌 집중 과정을 준비하세요.", link: "/operations" },
      { text: "게임잼 이벤트와 연계한 홍보를 추진하세요.", link: "/market" },
    ]
  },
  art: {
    field: "art",
    estimated_conversions: 22,
    previous_conversions: 25,
    target_conversion_rate: 0.30,
    current_demand_tier: "Low",
    conversion_rate_trend: [0.20,0.22,0.21,0.24,0.23,0.25,0.26,0.28],
    consultation_count_trend: [65,70,68,75,72,78,80,82],
    recommendations: [
      { text: "포트폴리오 리뷰 세션을 무료로 제공하세요.", link: "/simulator" },
      { text: "SNS 채널을 통한 작품 공유 이벤트를 진행하세요.", link: "/marketing" },
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
