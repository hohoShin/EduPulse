/**
 * Adapter Selector - Centralized Phase A/B Routing
 * 
 * Phase A: mockAdapter is the default (backend offline)
 * Phase B+: Switch to realAdapter when backend APIs are ready
 * 
 * Pages/components depend ONLY on this entrypoint, never directly on fetch or environment variables.
 */

import mockAdapter from './mockAdapter.js';
import realAdapter from './realAdapter.js';

// Phase A Default: Use mock adapter
// Set to 'real' when backend is ready (Phase B+)
const ACTIVE_ADAPTER = 'mock';

/**
 * Get the active adapter instance
 * @returns {Object} Active adapter with getDashboardSummary, getDemandChart, etc.
 */
function getAdapter() {
  if (ACTIVE_ADAPTER === 'real') {
    return realAdapter;
  }
  return mockAdapter;
}

// Export active adapter as default for page consumption
export default getAdapter();

// Also export getters for each surface individually (convenience for pages)
export async function getDashboardSummary(options) {
  const adapter = getAdapter();
  return adapter.getDashboardSummary(options);
}

export async function getDemandChart(options) {
  const adapter = getAdapter();
  return adapter.getDemandChart(options);
}

export async function getDashboardAlerts(options) {
  const adapter = getAdapter();
  return adapter.getDashboardAlerts(options);
}

export async function simulateDemand(input) {
  const adapter = getAdapter();
  return adapter.simulateDemand(input);
}

export async function getSystemStatus() {
  const adapter = getAdapter();
  return adapter.getSystemStatus();
}

export async function getLeadConversion(input) {
  const adapter = getAdapter();
  return adapter.getLeadConversion(input);
}

export async function getMarketingTiming(input) {
  const adapter = getAdapter();
  return adapter.getMarketingTiming(input);
}

export async function getClosureRisk(input) {
  const adapter = getAdapter();
  return adapter.getClosureRisk(input);
}

export async function getScheduleSuggest(input) {
  const adapter = getAdapter();
  return adapter.getScheduleSuggest(input);
}

export async function getDemographics(input) {
  const adapter = getAdapter();
  return adapter.getDemographics(input);
}

export async function getCompetitors(input) {
  const adapter = getAdapter();
  return adapter.getCompetitors(input);
}

export async function getOptimalStart(input) {
  const adapter = getAdapter();
  return adapter.getOptimalStart(input);
}

// Export both adapters for testing/debugging
export { mockAdapter, realAdapter };
