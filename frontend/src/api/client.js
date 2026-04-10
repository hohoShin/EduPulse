/**
 * API Client — Phase C
 *
 * Minimal fetch wrapper used by realAdapter.js.
 * Provides apiGet and apiPost with JSON parsing and error handling.
 * Error objects include a .status property for toErrorUIState() to consume.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Build a full URL from a path, appending to BASE_URL.
 * @param {string} path - e.g. '/api/v1/health'
 * @returns {string}
 */
function buildUrl(path) {
  const base = BASE_URL.replace(/\/$/, '');
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${base}${p}`;
}

/**
 * Create an error with a .status property for errors.js to classify.
 * @param {string} message
 * @param {number|null} status
 * @returns {Error & { status: number|null }}
 */
function makeError(message, status) {
  const err = new Error(message);
  err.status = status;
  return err;
}

/**
 * GET request — returns parsed JSON.
 * Throws an error with .status on non-ok responses.
 * @param {string} path - API path e.g. '/api/v1/health'
 * @returns {Promise<Object>}
 */
export async function apiGet(path) {
  const response = await fetch(buildUrl(path), {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    let detail = null;
    try {
      const body = await response.json();
      detail = body?.detail || body?.message || null;
    } catch {
      // ignore parse errors
    }
    throw makeError(detail || `HTTP ${response.status}`, response.status);
  }

  return response.json();
}

/**
 * POST request — sends JSON body, returns parsed JSON.
 * Throws an error with .status on non-ok responses.
 * @param {string} path - API path e.g. '/api/v1/simulator'
 * @param {Object} body - Request payload
 * @returns {Promise<Object>}
 */
export async function apiPost(path, body) {
  const response = await fetch(buildUrl(path), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let detail = null;
    try {
      const parsed = await response.json();
      detail = parsed?.detail || parsed?.message || null;
    } catch {
      // ignore parse errors
    }
    throw makeError(detail || `HTTP ${response.status}`, response.status);
  }

  return response.json();
}
