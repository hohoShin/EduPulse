/**
 * API Errors — Phase B
 *
 * Converts fetch/network errors into UIState error objects for pages/components.
 */

import { createUIState } from './viewModels.js';

/**
 * Convert a fetch/API error into a UIState with state:'error'.
 *
 * Rules:
 * - TypeError (network failure, no response) → '서버에 연결할 수 없습니다'
 * - err.status === 422 → '잘못된 입력입니다'
 * - err.status >= 500 → '서버 오류가 발생했습니다'
 * - Default → '알 수 없는 오류가 발생했습니다'
 *
 * @param {unknown} err - Any thrown value from apiGet / apiPost
 * @returns {import('./viewModels.js').UIState}
 */
export function toErrorUIState(err) {
  let message;

  if (err instanceof TypeError) {
    message = '서버에 연결할 수 없습니다';
  } else if (err && err.status === 422) {
    message = '잘못된 입력입니다';
  } else if (err && err.status >= 500) {
    message = '서버 오류가 발생했습니다';
  } else {
    message = '알 수 없는 오류가 발생했습니다';
  }

  return createUIState({ state: 'error', error: message, isDemo: false });
}
