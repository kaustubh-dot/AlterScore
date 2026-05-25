import {
  fetchHealth,
  fetchModelStats,
  fetchBaselineComparison,
  fetchFairnessReport,
  fetchDriftReport,
  fetchGlobalImportance,
  fetchScoreDistribution,
  fetchRocData,
  fetchPrCurve,
  fetchCalibrationCurve,
  fetchConfusionMatrix
} from "./api.js";

export async function runApiTests() {
  console.log("▶ Running api.js dashboard mock & failure tests...");

  const originalFetch = globalThis.fetch;

  // Test 1: Successful mock payloads
  let calledUrl = null;
  let calledOptions = null;

  globalThis.fetch = async (url, options) => {
    calledUrl = url;
    calledOptions = options;
    return {
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ status: "ok", test_mocked: true })
    };
  };

  const healthRes = await fetchHealth();
  if (!calledUrl.endsWith("/health")) throw new Error("fetchHealth mapped to incorrect endpoint URL");
  if (!healthRes.test_mocked) throw new Error("fetchHealth failed to resolve successful payload");
  console.log("  ✓ fetchHealth resolves mock payloads successfully");

  const statsRes = await fetchModelStats();
  if (!calledUrl.endsWith("/model-stats")) throw new Error("fetchModelStats URL mapping failed");
  console.log("  ✓ fetchModelStats resolves mock payloads successfully");

  const matrixRes = await fetchConfusionMatrix();
  if (!calledUrl.endsWith("/confusion-matrix")) throw new Error("fetchConfusionMatrix URL mapping failed");
  console.log("  ✓ fetchConfusionMatrix resolves mock payloads successfully");

  // Test 2: Failure state handling (503 Service Unavailable)
  globalThis.fetch = async (url, options) => {
    return {
      ok: false,
      status: 503,
      text: async () => JSON.stringify({
        error: {
          code: "ARTIFACTS_NOT_READY",
          message: "Saved metrics artifact is missing"
        }
      })
    };
  };

  try {
    await fetchModelStats();
    throw new Error("API service did not throw on 503 response");
  } catch (error) {
    if (error.status !== 503) throw new Error(`Expected error status 503, got ${error.status}`);
    if (error.message !== "Saved metrics artifact is missing") {
      throw new Error(`Expected error message 'Saved metrics artifact is missing', got: ${error.message}`);
    }
    if (error.payload?.error?.code !== "ARTIFACTS_NOT_READY") {
      throw new Error("Failed to map custom ARTIFACTS_NOT_READY error details");
    }
  }
  console.log("  ✓ API client throws structured ErrorResponse on 503 Service Unavailable");

  // Test 3: Failure state handling (500 Internal Server Error)
  globalThis.fetch = async (url, options) => {
    return {
      ok: false,
      status: 500,
      text: async () => JSON.stringify({
        error: {
          code: "ANALYTICS_PAYLOAD_INVALID",
          message: "Saved metrics payload is corrupt or invalid"
        }
      })
    };
  };

  try {
    await fetchConfusionMatrix();
    throw new Error("API service did not throw on 500 response");
  } catch (error) {
    if (error.status !== 500) throw new Error(`Expected error status 500, got ${error.status}`);
    if (error.payload?.error?.code !== "ANALYTICS_PAYLOAD_INVALID") {
      throw new Error("Failed to map custom ANALYTICS_PAYLOAD_INVALID error details");
    }
  }
  console.log("  ✓ API client throws structured ErrorResponse on 500 Internal Server Error");

  // Restore fetch
  globalThis.fetch = originalFetch;
  console.log("✓ All api.js tests PASSED!\n");
}
