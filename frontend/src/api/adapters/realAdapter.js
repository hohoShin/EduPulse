/**
 * Real Adapter - Phase B+ Placeholder
 * 
 * Exposes the same method signatures as mockAdapter.
 * In Phase B+, these will connect to actual backend endpoints.
 * For now, all methods return controlled placeholder/error states.
 */

import { createUIState } from '../viewModels.js';

/**
 * Get dashboard summary cards from backend
 * Phase B+: Will call GET /api/v1/dashboard/summary
 * @returns {Promise<Object>} UIState with summary card data
 */
export async function getDashboardSummary() {
  // Phase A: Not implemented - return placeholder
  return createUIState({
    state: 'error',
    error: 'Real adapter not yet implemented. Switch to mock adapter for Phase A.',
    isDemo: false,
  });
}

/**
 * Get demand forecast chart data from backend
 * Phase B+: Will call GET /api/v1/dashboard/demand-chart
 * @returns {Promise<Object>} UIState with chart point data
 */
export async function getDemandChart() {
  // Phase A: Not implemented - return placeholder
  return createUIState({
    state: 'error',
    error: 'Real adapter not yet implemented. Switch to mock adapter for Phase A.',
    isDemo: false,
  });
}

/**
 * Get dashboard alerts from backend
 * Phase B+: Will call GET /api/v1/dashboard/alerts
 * @returns {Promise<Object>} UIState with alert items
 */
export async function getDashboardAlerts() {
  // Phase A: Not implemented - return placeholder
  return createUIState({
    state: 'error',
    error: 'Real adapter not yet implemented. Switch to mock adapter for Phase A.',
    isDemo: false,
  });
}

/**
 * Run a demand simulator prediction via backend
 * Phase B+: Will call POST /api/v1/simulator with { courseName, field, startDate }
 * @returns {Promise<Object>} UIState with simulator result
 */
export async function simulateDemand() {
   // Phase A: Not implemented - return placeholder
   return createUIState({
     state: 'error',
     error: 'Real adapter not yet implemented. Switch to mock adapter for Phase A.',
     isDemo: false,
   });
 }

/**
 * Get system health / backend connectivity status
 * Phase B+: Will call GET /api/v1/health
 * @returns {Promise<Object>} UIState with service status items
 */
export async function getSystemStatus() {
  // Phase A: Not implemented - return placeholder
  return createUIState({
    state: 'error',
    error: 'Real adapter not yet implemented. Switch to mock adapter for Phase A.',
    isDemo: false,
  });
}

/**
 * Real adapter export - same surface as mockAdapter, non-breaking placeholder
 */
export default {
  getDashboardSummary,
  getDemandChart,
  getDashboardAlerts,
  simulateDemand,
  getSystemStatus,
};
