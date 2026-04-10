/**
 * Hybrid Adapter - Phase C Transition
 *
 * Dashboard 3 methods (getDashboardSummary, getDemandChart, getDashboardAlerts)
 * continue to use mockAdapter while the backend dashboard endpoints are not yet ready.
 *
 * All remaining 9 methods route to realAdapter which calls the live backend.
 */

import mockAdapter from './mockAdapter.js';
import realAdapter from './realAdapter.js';

/**
 * Dashboard surfaces — still backed by mock fixtures
 */
export async function getDashboardSummary(options) {
  return mockAdapter.getDashboardSummary(options);
}

export async function getDemandChart(options) {
  return mockAdapter.getDemandChart(options);
}

export async function getDashboardAlerts(options) {
  return mockAdapter.getDashboardAlerts(options);
}

/**
 * Remaining surfaces — routed to real backend
 */
export async function simulateDemand(input) {
  return realAdapter.simulateDemand(input);
}

export async function getSystemStatus() {
  return realAdapter.getSystemStatus();
}

export async function getLeadConversion(input) {
  return realAdapter.getLeadConversion(input);
}

export async function getMarketingTiming(input) {
  return realAdapter.getMarketingTiming(input);
}

export async function getClosureRisk(input) {
  return realAdapter.getClosureRisk(input);
}

export async function getScheduleSuggest(input) {
  return realAdapter.getScheduleSuggest(input);
}

export async function getDemographics(input) {
  return realAdapter.getDemographics(input);
}

export async function getCompetitors(input) {
  return realAdapter.getCompetitors(input);
}

export async function getOptimalStart(input) {
  return realAdapter.getOptimalStart(input);
}

/**
 * Hybrid adapter export
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
