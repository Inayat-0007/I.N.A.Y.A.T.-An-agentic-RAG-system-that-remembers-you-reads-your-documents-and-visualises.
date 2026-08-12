/** Shared headers for mutating API calls (optional INAYAT_API_KEY). */
export function apiHeaders(extra = {}) {
  const headers = { ...extra };
  const key = import.meta.env.VITE_INAYAT_API_KEY;
  if (key) {
    headers["X-INAYAT-KEY"] = key;
  }
  return headers;
}
