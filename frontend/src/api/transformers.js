/**
 * API Transformers — Phase B
 *
 * Backend 응답을 UI가 기대하는 형태로 변환한다.
 * 핵심 원칙: 페이지는 mock fixture와 동일한 snake_case 속성을 사용하므로
 * transformer 출력도 snake_case를 유지한다.
 * 예외: createSimulatorResult / createStatusItem은 viewModels 팩토리가 camelCase를 정의한다.
 */

import { createStatusItem, createSimulatorResult } from './viewModels.js';

// ---------------------------------------------------------------------------
// Case conversion utilities (요청 body 전송용)
// ---------------------------------------------------------------------------

function camelToSnakeStr(str) {
  return str.replace(/([A-Z])/g, (c) => `_${c.toLowerCase()}`);
}

/**
 * Recursively convert all object keys from camelCase to snake_case.
 * Used to convert frontend input → backend request body.
 * @param {*} obj
 * @returns {*}
 */
export function camelToSnake(obj) {
  if (obj === null || obj === undefined) return obj;
  if (Array.isArray(obj)) return obj.map(camelToSnake);
  if (typeof obj !== 'object') return obj;

  return Object.fromEntries(
    Object.entries(obj).map(([k, v]) => [camelToSnakeStr(k), camelToSnake(v)]),
  );
}

// ---------------------------------------------------------------------------
// Endpoint-specific transform functions
// ---------------------------------------------------------------------------

/**
 * Transform GET /api/v1/health → StatusItem[] (viewModels 팩토리 사용).
 *
 * Backend: { status, models_loaded: string[], db_connected: bool, memory_usage_mb: float }
 */
export function transformHealthResponse(raw) {
  const now = new Date().toISOString();
  return [
    createStatusItem('API 서버', raw.status === 'ok' ? 'ok' : 'degraded', now, {}),
    createStatusItem(
      '모델 로딩',
      raw.models_loaded?.length > 0 ? 'ok' : 'degraded',
      now,
      { models: raw.models_loaded ?? [] },
    ),
    createStatusItem('데이터베이스', raw.db_connected ? 'ok' : 'down', now, {}),
    createStatusItem('메모리', 'ok', now, { usage: raw.memory_usage_mb }),
  ];
}

/**
 * Transform POST /api/v1/simulation/simulate → SimulatorResult (viewModels 팩토리 사용).
 *
 * Backend SimulateResponse:
 *   { baseline, optimistic, pessimistic, market_context }
 *   Each scenario: { scenario, predicted_enrollment, demand_tier, estimated_revenue }
 */
export function transformSimulateResponse(raw, courseName = '', field = '') {
  const baseline = raw.baseline ?? {};
  const optimistic = raw.optimistic ?? {};
  const pessimistic = raw.pessimistic ?? {};

  return createSimulatorResult({
    courseName,
    field,
    predictedCount: baseline.predicted_enrollment ?? 0,
    demandTier: baseline.demand_tier ?? 'MID',
    confidenceInterval: {
      lower: pessimistic.predicted_enrollment ?? 0,
      upper: optimistic.predicted_enrollment ?? 0,
    },
    modelUsed: 'ensemble',
    predictionDate: new Date().toISOString(),
    marketing: null,
    operations: null,
  });
}

/**
 * Transform POST /api/v1/marketing/lead-conversion → mock fixture 형태.
 *
 * Backend: { field, estimated_conversions,
 *            consultation_count_trend: float[], recommendations: string[] }
 * Fixture: snake_case + recommendations: {text, link}[] + previous_conversions 등 추가 필드
 */
export function transformLeadConversionResponse(raw) {
  return {
    field: raw.field,
    estimated_conversions: raw.estimated_conversions,
    previous_conversions: null,
    current_demand_tier: null,
    consultation_count_trend: raw.consultation_count_trend ?? [],
    recommendations: (raw.recommendations ?? []).map((text) => ({ text, link: null })),
  };
}

/**
 * Transform POST /api/v1/demand/closure-risk → mock fixture 형태.
 *
 * Backend: { risk_score, risk_level, contributing_factors, recommendation }
 * Fixture: snake_case + risk_trend, predicted_enrollment, min_enrollment 추가
 */
export function transformClosureRiskResponse(raw) {
  return {
    risk_score: raw.risk_score,
    risk_level: raw.risk_level,
    risk_trend: null,
    predicted_enrollment: null,
    min_enrollment: null,
    contributing_factors: raw.contributing_factors ?? [],
    recommendation: raw.recommendation,
  };
}

/**
 * Transform POST /api/v1/simulation/competitors → mock fixture 형태.
 *
 * Backend: { field, competitor_openings, competitor_avg_price, saturation_index, recommendation }
 * Fixture: snake_case + previous_openings, previous_avg_price 추가
 */
export function transformCompetitorResponse(raw) {
  return {
    field: raw.field,
    competitor_openings: raw.competitor_openings,
    previous_openings: null,
    competitor_avg_price: raw.competitor_avg_price,
    previous_avg_price: null,
    saturation_index: raw.saturation_index,
    recommendation: raw.recommendation,
  };
}

/**
 * Transform POST /api/v1/simulation/demographics → mock fixture 형태.
 *
 * Backend와 fixture 모두 snake_case이므로 pass-through.
 * Backend에 없는 total_students 필드만 null로 추가.
 */
export function transformDemographicsResponse(raw) {
  return {
    ...raw,
    total_students: raw.total_students ?? null,
  };
}

/**
 * Transform POST /api/v1/schedule/suggest → mock fixture 형태.
 *
 * Backend: { course_name, start_date, predicted_enrollment, required_instructors,
 *            required_classrooms, assignment_plan: { classes: [...], summary } }
 * Fixture: snake_case 그대로.
 */
export function transformScheduleResponse(raw) {
  return {
    course_name: raw.course_name,
    start_date: raw.start_date,
    predicted_enrollment: raw.predicted_enrollment,
    required_instructors: raw.required_instructors,
    required_classrooms: raw.required_classrooms,
    assignment_plan: raw.assignment_plan ?? { classes: [], summary: '' },
  };
}

/**
 * Transform POST /api/v1/marketing/timing → mock fixture 형태.
 *
 * Backend: { course_name, demand_tier, ad_launch_weeks_before, earlybird_duration_days, discount_rate }
 * Fixture: snake_case (course_name 제외, 페이지에서 미사용).
 */
export function transformMarketingTimingResponse(raw) {
  return {
    demand_tier: raw.demand_tier,
    ad_launch_weeks_before: raw.ad_launch_weeks_before,
    earlybird_duration_days: raw.earlybird_duration_days,
    discount_rate: raw.discount_rate,
  };
}

/**
 * Transform POST /api/v1/simulation/optimal-start → mock fixture 형태.
 *
 * Backend: { top_candidates: [{date, predicted_enrollment, demand_tier, composite_score}] }
 * Fixture: snake_case 그대로.
 */
export function transformOptimalStartResponse(raw) {
  return {
    top_candidates: raw.top_candidates ?? [],
  };
}

/**
 * Transform POST /api/v1/demand/predict → snake_case pass-through.
 *
 * Backend: { course_name, field, predicted_enrollment, demand_tier,
 *            confidence_interval: {lower, upper}, model_used, prediction_date }
 */
export function transformDemandResponse(raw) {
  return raw;
}
