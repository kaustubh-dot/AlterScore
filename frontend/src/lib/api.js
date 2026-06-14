import axios from 'axios';

function normalizeApiBaseUrl(rawValue) {
  if (!rawValue) {
    return '/api';
  }

  const trimmed = rawValue.trim().replace(/\/+$/, '');
  if (!trimmed) {
    return '/api';
  }

  return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
}

export const API_BASE_URL = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
});

export function getHealthUrl() {
  return `${API_BASE_URL}/health`;
}

export default api;
