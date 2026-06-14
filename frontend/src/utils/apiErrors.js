export function formatApiError(error, fallbackMessage = 'Request failed.') {
  if (error?.response) {
    const { status, statusText, data } = error.response;
    const details = data?.detail;

    if (status === 422) {
      if (Array.isArray(details)) {
        return `Validation failed: ${details.map((item) => {
          const path = Array.isArray(item?.loc) ? item.loc.slice(1).join('.') : 'request';
          return `${path}: ${item?.msg ?? 'invalid value'}`;
        }).join(', ')}`;
      }
      if (typeof details === 'string') {
        return `Validation failed: ${details}`;
      }
    }

    const apiMessage = data?.error?.message || data?.message;
    if (typeof apiMessage === 'string' && apiMessage.trim()) {
      return apiMessage;
    }

    return `Server error: ${statusText || fallbackMessage} (Status: ${status})`;
  }

  return 'Unable to reach the scoring backend. Check the deployed API URL and CORS configuration, then try again.';
}
