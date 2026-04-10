/**
 * Mock Adapter - Phase A Default
 * 
 * Sources demo data from Task 2 fixtures for all surfaces.
 * This is the Phase A default adapter and requires no backend connectivity.
 */

import {
  dashboardSummarySuccess,
  dashboardSummaryLoading,
  dashboardSummaryEmpty,
  dashboardSummaryError,
  demandChartSuccess,
  demandChartLoading,
  demandChartEmpty,
  demandChartError,
  dashboardAlertsSuccess,
  dashboardAlertsLoading,
  dashboardAlertsEmpty,
  dashboardAlertsError,
} from '../../fixtures/dashboardStates.js';

import {
  simulatorResultSuccess,
  simulatorError,
} from '../../fixtures/simulatorStates.js';

import {
  systemStatusSuccess,
} from '../../fixtures/systemStatusStates.js';

import {
  leadConversionSuccess,
  marketingTimingSuccess,
} from '../../fixtures/marketingStates.js';

import {
  closureRiskSuccess,
  scheduleSuggestSuccess,
} from '../../fixtures/operationsStates.js';

import {
  demographicsSuccess,
  competitorsSuccess,
  optimalStartSuccess,
} from '../../fixtures/marketStates.js';

/**
 * Get dashboard summary cards (loading, success, empty, error states available)
 * @returns {Promise<Object>} UIState with summary card data
 */
export async function getDashboardSummary(options = {}) {
  // Simulate network delay for realism
  await new Promise(resolve => setTimeout(resolve, 100));
  
  if (options.forceState === 'loading') return dashboardSummaryLoading;
  if (options.forceState === 'empty') return dashboardSummaryEmpty;
  if (options.forceState === 'error') return dashboardSummaryError;
  
  return dashboardSummarySuccess;
}

/**
 * Get demand forecast chart data (loading, success, empty, error states available)
 * @returns {Promise<Object>} UIState with chart point data
 */
export async function getDemandChart(options = {}) {
  // Simulate network delay for realism
  await new Promise(resolve => setTimeout(resolve, 150));
  
  if (options.forceState === 'loading') return demandChartLoading;
  if (options.forceState === 'empty') return demandChartEmpty;
  if (options.forceState === 'error') return demandChartError;
  
  return demandChartSuccess;
}

/**
 * Get dashboard alerts (closure risk, marketing timing, etc.)
 * @returns {Promise<Object>} UIState with alert items
 */
export async function getDashboardAlerts(options = {}) {
  // Simulate network delay for realism
  await new Promise(resolve => setTimeout(resolve, 100));
  
  if (options.forceState === 'loading') return dashboardAlertsLoading;
  if (options.forceState === 'empty') return dashboardAlertsEmpty;
  if (options.forceState === 'error') return dashboardAlertsError;
  
  return dashboardAlertsSuccess;
}

/**
 * Run a demand simulator prediction
 * Accepts course info and returns prediction, staffing, and marketing guidance
 * @param {Object} input - { courseName, field, startDate }
 * @returns {Promise<Object>} UIState with simulator result
 */
export async function simulateDemand(input) {
  if (!input || !input.courseName || !input.field) {
    return simulatorError;
  }

  if (input.courseName.toLowerCase().includes('error')) {
    return simulatorError;
  }

  await new Promise(resolve => setTimeout(resolve, 200));

  if (input.courseName.toLowerCase().includes('low')) {
    return {
      ...simulatorResultSuccess,
      data: {
        ...simulatorResultSuccess.data,
        courseName: input.courseName,
        field: input.field,
        predictedCount: 12,
        demandTier: 'Low',
        confidenceInterval: { lower: 5, upper: 18 },
        operations: { instructors: 1, classrooms: 1 },
      }
    };
  }

  return {
    ...simulatorResultSuccess,
    data: {
      ...simulatorResultSuccess.data,
      courseName: input.courseName,
      field: input.field,
    }
  };
}

/**
 * Get system health / backend connectivity status
 * @returns {Promise<Object>} UIState with service status items
 */
export async function getSystemStatus() {
  // Simulate network delay for realism
  await new Promise(resolve => setTimeout(resolve, 120));
  return systemStatusSuccess;
}

export async function getLeadConversion(input = {}) {
  await new Promise(resolve => setTimeout(resolve, 150));
  return leadConversionSuccess(input.field || 'coding');
}

export async function getMarketingTiming(input = {}) {
  await new Promise(resolve => setTimeout(resolve, 100));
  return marketingTimingSuccess(input.field || 'coding');
}

export async function getClosureRisk(input = {}) {
  await new Promise(resolve => setTimeout(resolve, 200));
  return closureRiskSuccess;
}

export async function getScheduleSuggest(input = {}) {
  await new Promise(resolve => setTimeout(resolve, 150));
  return scheduleSuggestSuccess;
}

export async function getDemographics(input = {}) {
  await new Promise(resolve => setTimeout(resolve, 150));
  return demographicsSuccess(input.field || 'coding');
}

export async function getCompetitors(input = {}) {
  await new Promise(resolve => setTimeout(resolve, 100));
  return competitorsSuccess(input.field || 'coding');
}

export async function getOptimalStart(input = {}) {
  await new Promise(resolve => setTimeout(resolve, 200));
  return optimalStartSuccess(input.field || 'coding');
}

/**
 * Mock adapter export - includes all surfaces required for Phase A
 */
export default {
  getDashboardSummary,
  getDemandChart,
  getDashboardAlerts,
  simulateDemand,
  getSystemStatus,
  getLeadConversion,
  getMarketingTiming,
  getClosureRisk,
  getScheduleSuggest,
  getDemographics,
  getCompetitors,
  getOptimalStart,
};
