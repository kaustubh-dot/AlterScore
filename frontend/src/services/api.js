export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  let payload = null;
  const text = await response.text();
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = { message: text };
    }
  }

  if (!response.ok) {
    const error = new Error(payload?.error?.message || payload?.message || "Request failed");
    error.status = response.status;
    error.payload = payload;
    throw error;
  }

  return payload;
}

export function fetchHealth() {
  return request("/health", { method: "GET" });
}

export function submitScore(payload) {
  return request("/score", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchModelStats() {
  return request("/model-stats", { method: "GET" });
}

export function fetchBaselineComparison() {
  return request("/baseline-comparison", { method: "GET" });
}

export function fetchFairnessReport() {
  return request("/fairness-report", { method: "GET" });
}

export function fetchDriftReport() {
  return request("/drift-report", { method: "GET" });
}

export function fetchGlobalImportance() {
  return request("/global-importance", { method: "GET" });
}

export function fetchScoreDistribution() {
  return request("/score-distribution", { method: "GET" });
}

export function fetchRocData() {
  return request("/roc-data", { method: "GET" });
}

export function fetchPrCurve() {
  return request("/pr-curve", { method: "GET" });
}

export function fetchCalibrationCurve() {
  return request("/calibration-curve", { method: "GET" });
}

export function fetchConfusionMatrix() {
  return request("/confusion-matrix", { method: "GET" });
}
