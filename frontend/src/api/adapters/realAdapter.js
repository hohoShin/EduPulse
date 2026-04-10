/**
 * Real Adapter — Phase C + D
 *
 * Fully implemented adapter that calls the EduPulse FastAPI backend.
 * Mirrors the same method surface as mockAdapter.js so pages are unaffected
 * when ACTIVE_ADAPTER switches from 'mock' to 'real'.
 *
 * 핵심 원칙: 페이지는 mock fixture의 snake_case 속성을 사용하므로
 * adapter 출력도 동일한 형태를 유지한다.
 */

import { createUIState, createSummaryCard, createChartPoint, createAlertItem } from '../viewModels.js';
import { apiGet, apiPost } from '../client.js';
import {
  transformHealthResponse,
  transformSimulateResponse,
  transformLeadConversionResponse,
  transformClosureRiskResponse,
  transformCompetitorResponse,
  transformDemographicsResponse,
  transformScheduleResponse,
  transformMarketingTimingResponse,
  transformOptimalStartResponse,
  transformDemandResponse,
} from '../transformers.js';
import { toErrorUIState } from '../errors.js';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(d) {
  if (!d) return new Date().toISOString().split('T')[0];
  if (d instanceof Date) return d.toISOString().split('T')[0];
  return String(d);
}

function futureDate(weeks) {
  const d = new Date();
  d.setDate(d.getDate() + weeks * 7);
  return d.toISOString().split('T')[0];
}

function today() {
  return new Date().toISOString().split('T')[0];
}

// ---------------------------------------------------------------------------
// Group 1 — Direct mapping (5 methods)
// ---------------------------------------------------------------------------

async function getSystemStatus() {
  try {
    const raw = await apiGet('/api/v1/health');
    return createUIState({ state: 'success', data: transformHealthResponse(raw), isDemo: false });
  } catch (err) {
    return toErrorUIState(err);
  }
}

async function getLeadConversion({ field } = {}) {
  try {
    const raw = await apiPost('/api/v1/marketing/lead-conversion', { field: field || 'coding' });
    return createUIState({ state: 'success', data: transformLeadConversionResponse(raw), isDemo: false });
  } catch (err) {
    return toErrorUIState(err);
  }
}

async function getDemographics({ field } = {}) {
  try {
    const raw = await apiPost('/api/v1/simulation/demographics', { field: field || 'coding' });
    return createUIState({ state: 'success', data: transformDemographicsResponse(raw), isDemo: false });
  } catch (err) {
    return toErrorUIState(err);
  }
}

async function getCompetitors({ field } = {}) {
  try {
    const raw = await apiPost('/api/v1/simulation/competitors', { field: field || 'coding' });
    return createUIState({ state: 'success', data: transformCompetitorResponse(raw), isDemo: false });
  } catch (err) {
    return toErrorUIState(err);
  }
}

async function getClosureRisk({ courseName, field, startDate } = {}) {
  try {
    const raw = await apiPost('/api/v1/demand/closure-risk', {
      course_name: courseName || '기본과정',
      start_date: formatDate(startDate) || futureDate(4),
      field: field || 'coding',
    });
    return createUIState({ state: 'success', data: transformClosureRiskResponse(raw), isDemo: false });
  } catch (err) {
    return toErrorUIState(err);
  }
}

// ---------------------------------------------------------------------------
// Group 2 — Chaining (3 methods)
// ---------------------------------------------------------------------------

async function getScheduleSuggest({ courseName, field, startDate } = {}) {
  try {
    const demandRaw = await apiPost('/api/v1/demand/predict', {
      course_name: courseName || '기본과정',
      start_date: formatDate(startDate),
      field: field || 'coding',
    });

    const scheduleRaw = await apiPost('/api/v1/schedule/suggest', {
      course_name: courseName || '기본과정',
      start_date: formatDate(startDate),
      predicted_enrollment: demandRaw.predicted_enrollment,
    });

    return createUIState({ state: 'success', data: transformScheduleResponse(scheduleRaw), isDemo: false });
  } catch (err) {
    return toErrorUIState(err);
  }
}

/**
 * Parallel marketing timing for all three demand tiers.
 * Returns an ARRAY (matching mock fixture shape), not an object.
 */
async function getMarketingTiming({ field } = {}) {
  try {
    const startDate = futureDate(8);
    const [r1, r2, r3] = await Promise.all([
      apiPost('/api/v1/marketing/timing', { course_name: '기본과정', start_date: startDate, demand_tier: 'HIGH' }),
      apiPost('/api/v1/marketing/timing', { course_name: '기본과정', start_date: startDate, demand_tier: 'MID' }),
      apiPost('/api/v1/marketing/timing', { course_name: '기본과정', start_date: startDate, demand_tier: 'LOW' }),
    ]);

    return createUIState({
      state: 'success',
      data: [
        transformMarketingTimingResponse(r1),
        transformMarketingTimingResponse(r2),
        transformMarketingTimingResponse(r3),
      ],
      isDemo: false,
    });
  } catch (err) {
    return toErrorUIState(err);
  }
}

async function getOptimalStart({ field, startDate, endDate } = {}) {
  try {
    const raw = await apiPost('/api/v1/simulation/optimal-start', {
      course_name: '기본과정',
      field: field || 'coding',
      search_window_start: startDate || today(),
      search_window_end: endDate || futureDate(8),
    });
    return createUIState({ state: 'success', data: transformOptimalStartResponse(raw), isDemo: false });
  } catch (err) {
    return toErrorUIState(err);
  }
}

// ---------------------------------------------------------------------------
// Group 3 — Complex chaining (1 method)
// ---------------------------------------------------------------------------

async function simulateDemand({ courseName, field, startDate } = {}) {
  try {
    const raw = await apiPost('/api/v1/simulation/simulate', {
      course_name: courseName,
      field,
      start_date: formatDate(startDate),
      price_per_student: 500000,
    });

    const result = transformSimulateResponse(raw, courseName, field);

    const [mktRaw, schRaw] = await Promise.all([
      apiPost('/api/v1/marketing/timing', {
        course_name: courseName,
        start_date: formatDate(startDate),
        demand_tier: raw.baseline?.demand_tier,
      }),
      apiPost('/api/v1/schedule/suggest', {
        course_name: courseName,
        start_date: formatDate(startDate),
        predicted_enrollment: raw.baseline?.predicted_enrollment,
      }),
    ]);

    // createSimulatorResult expects camelCase sub-objects
    result.marketing = {
      adWeeksBefore: mktRaw.ad_launch_weeks_before,
      earlybirdDays: mktRaw.earlybird_duration_days,
      discountRate: mktRaw.discount_rate,
    };
    result.operations = {
      instructors: schRaw.required_instructors,
      classrooms: schRaw.required_classrooms,
    };

    return createUIState({ state: 'success', data: result, isDemo: false });
  } catch (err) {
    return toErrorUIState(err);
  }
}

// ---------------------------------------------------------------------------
// Group 4 — Dashboard (3 methods, Phase D)
// ---------------------------------------------------------------------------

async function getDashboardSummary({ field } = {}) {
  try {
    const f = field || 'coding';
    const [, compRaw, demandRaw] = await Promise.all([
      apiPost('/api/v1/simulation/demographics', { field: f }),
      apiPost('/api/v1/simulation/competitors', { field: f }),
      apiPost('/api/v1/demand/predict', {
        course_name: '기본과정',
        start_date: futureDate(4),
        field: f,
      }),
    ]);

    const cards = [
      createSummaryCard(
        'total-students', '예상 수강생',
        demandRaw.predicted_enrollment, '명',
        null, null, null, 'users',
      ),
      createSummaryCard(
        'competitor-count', '경쟁 강좌',
        compRaw.competitor_openings, '개',
        null, null, null, 'chart',
      ),
      createSummaryCard(
        'demand-index', '수요 지수',
        demandRaw.demand_tier, null,
        null, null, null, 'trending',
      ),
    ];

    return createUIState({ state: 'success', data: cards, isDemo: false });
  } catch (err) {
    return toErrorUIState(err);
  }
}

async function getDemandChart({ field } = {}) {
  try {
    const raw = await apiPost('/api/v1/simulation/optimal-start', {
      course_name: '기본과정',
      field: field || 'coding',
      search_window_start: today(),
      search_window_end: futureDate(8),
    });

    const candidates = raw.top_candidates ?? [];
    const points = candidates
      .slice(0, 5)
      .map((c) => createChartPoint(c.date, c.predicted_enrollment, null, null, c.demand_tier));

    const state = points.length === 0 ? 'empty' : 'success';
    return createUIState({ state, data: points, isDemo: false });
  } catch (err) {
    return toErrorUIState(err);
  }
}

async function getDashboardAlerts({ field } = {}) {
  try {
    const raw = await apiPost('/api/v1/demand/closure-risk', {
      course_name: '기본과정',
      start_date: futureDate(4),
      field: field || 'coding',
    });

    if (raw.risk_level === 'high') {
      return createUIState({
        state: 'success',
        data: [createAlertItem('closure-1', '폐강 위험', raw.recommendation, 'critical', new Date().toISOString())],
        isDemo: false,
      });
    }

    if (raw.risk_level === 'medium') {
      return createUIState({
        state: 'success',
        data: [createAlertItem('closure-1', '폐강 주의', raw.recommendation, 'warning', new Date().toISOString())],
        isDemo: false,
      });
    }

    return createUIState({ state: 'empty', isDemo: false });
  } catch (err) {
    return toErrorUIState(err);
  }
}

// ---------------------------------------------------------------------------
// Default export
// ---------------------------------------------------------------------------

export default {
  getSystemStatus,
  getLeadConversion,
  getDemographics,
  getCompetitors,
  getClosureRisk,
  getScheduleSuggest,
  getMarketingTiming,
  getOptimalStart,
  simulateDemand,
  getDashboardSummary,
  getDemandChart,
  getDashboardAlerts,
};
