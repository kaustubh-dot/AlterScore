export function formatApiError(error, fallbackMessage = 'Request failed.') {
  if (isCancellationError(error)) return 'The request was cancelled.';
  if (error?.code === 'release_mismatch') {
    return 'The assessment client and scoring service releases do not match. Please try again later.';
  }

  if (error?.response) {
    const { status, statusText } = error.response;
    const code = getApiErrorCode(error);

    if (code === 'unsupported_version') {
      return 'This assessment version is not supported. Please request a fresh form.';
    }
    if (isAttemptLifecycleError(error)) {
      return 'This assessment attempt is no longer available. Please request a fresh form.';
    }
    if (code === 'unknown_option' || code === 'invalid_response') {
      return 'The issued response set no longer matches this attempt. Please request a fresh form.';
    }
    if (code === 'rate_limited') {
      const retryAfter = getRetryAfterSeconds(error);
      return retryAfter
        ? `Too many requests. You can try again immediately; the server suggests retrying in about ${retryAfter} seconds.`
        : 'Too many requests. You can try again shortly.';
    }
    if (code === 'not_ready' || code === 'form_unavailable') {
      return 'The assessment service is temporarily unavailable. Please try again.';
    }

    if (status === 422) {
      return 'The submitted request was invalid. Please request a fresh form.';
    }

    if (status >= 400 && status < 500) {
      return `Request could not be completed (Status: ${status}).`;
    }

    return `Server error: ${statusText ? 'The scoring service returned an error' : fallbackMessage} (Status: ${status})`;
  }

  if (isTimeoutError(error)) {
    return 'The request timed out. Start a fresh attempt and try again.';
  }

  return 'Unable to reach the scoring backend. Check the deployed API URL and CORS configuration, then try again.';
}

export function getApiErrorCode(error) {
  const code = error?.response?.data?.error?.code;
  return typeof code === 'string' ? code : null;
}

export function getRetryAfterSeconds(error) {
  const value = error?.response?.data?.error?.details?.retry_after_seconds;
  return Number.isInteger(value) && value > 0 ? value : null;
}

export function isAttemptLifecycleError(error) {
  return ['attempt_expired', 'attempt_consumed', 'attempt_stale'].includes(getApiErrorCode(error));
}

export function isCancellationError(error) {
  return error?.code === 'ERR_CANCELED'
    || error?.name === 'CanceledError'
    || error?.name === 'AbortError';
}

export function isTimeoutError(error) {
  return error?.code === 'ECONNABORTED'
    || error?.code === 'ETIMEDOUT'
    || (typeof error?.message === 'string' && error.message.toLowerCase().includes('timeout'));
}
