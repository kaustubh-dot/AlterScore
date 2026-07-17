import axios from 'axios';
import { isMatchingReleaseMetadata } from './releaseMetadata.js';

export function normalizeApiBaseUrl(rawValue) {
  if (!rawValue) {
    return '/api';
  }

  const trimmed = rawValue.trim().replace(/\/+$/, '');
  if (!trimmed) {
    return '/api';
  }

  if (trimmed.startsWith('/')) {
    return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
  }

  try {
    const configuredUrl = new URL(trimmed);
    const loopbackHttp = configuredUrl.protocol === 'http:'
      && ['localhost', '127.0.0.1', '[::1]'].includes(configuredUrl.hostname);
    if (configuredUrl.protocol !== 'https:' && !loopbackHttp) return null;
    return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
  } catch {
    return null;
  }
}

const configuredApiBaseUrl = import.meta.env?.VITE_API_BASE_URL;
const normalizedApiBaseUrl = normalizeApiBaseUrl(configuredApiBaseUrl);
const apiConfigurationError = configuredApiBaseUrl && !normalizedApiBaseUrl
  ? new Error('The assessment API must use an HTTPS URL.')
  : null;

export const API_BASE_URL = normalizedApiBaseUrl || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

function getSecureApiTransportError() {
  if (apiConfigurationError) return apiConfigurationError;
  if (API_BASE_URL.startsWith('/')
    && typeof window !== 'undefined'
    && window.location.protocol !== 'https:'
    && !['localhost', '127.0.0.1', '[::1]'].includes(window.location.hostname)) {
    return new Error('The assessment API requires HTTPS before an attempt token can be sent.');
  }
  return null;
}

function assertMatchingRelease(response) {
  if (!isMatchingReleaseMetadata(response?.data)) {
    const error = new Error('The frontend and assessment API releases do not match.');
    error.code = 'release_mismatch';
    throw error;
  }
  return response;
}

export function fetchV2Live(config = {}) {
  const transportError = getSecureApiTransportError();
  if (transportError) return Promise.reject(transportError);
  return api.get('/live', config).then(assertMatchingRelease);
}

export function fetchV2AssessmentForm(config = {}) {
  const transportError = getSecureApiTransportError();
  if (transportError) return Promise.reject(transportError);
  return fetchV2Live(config).then(() => api.get('/v2/assessment/form', config).then(assertMatchingRelease));
}

export function submitV2Assessment(form, submission, config = {}) {
  const transportError = getSecureApiTransportError();
  if (transportError) return Promise.reject(transportError);
  const headers = {
    ...(config.headers || {}),
    Authorization: `Bearer ${form.attempt_token}`,
  };
  return api.post('/v2/assessment/score', submission, { ...config, headers })
    .then(assertMatchingRelease);
}

export function getV2VerificationUrl(resultId) {
  return `${API_BASE_URL}/v2/results/verify/${encodeURIComponent(resultId)}`;
}
