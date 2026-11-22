const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// Shown when the REST API cannot be reached at all (network down, container stopped, nginx 502/503/504)
export const SERVER_UNREACHABLE_MESSAGE = 'The server is not reachable. Please try again later.';

// Gateway errors come from nginx, not from the REST API, so their body has no useful message
const GATEWAY_ERROR_STATUSES = new Set([502, 503, 504]);

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    // 0 = no HTTP response at all (network error)
    this.status = status;
  }
}

// fetch() only rejects on network errors (it resolves for 4xx/5xx); turn the browser's
// "Failed to fetch" TypeError into an ApiError with a message the user can understand
async function safeFetch(url, options) {
  try {
    return await fetch(url, options);
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw error; // cancelled on purpose (e.g. component unmounted), not a server problem
    }
    throw new ApiError(SERVER_UNREACHABLE_MESSAGE, 0);
  }
}

async function handleResponse(response) {
  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get('content-type') || '';
  const body = contentType.includes('application/json') ? await response.json().catch(() => null) : null;

  if (!response.ok) {
    const fieldErrors = body?.errors ? Object.values(body.errors).join(' ') : null;
    const fallback = GATEWAY_ERROR_STATUSES.has(response.status)
      ? SERVER_UNREACHABLE_MESSAGE
      : `Request failed with status ${response.status}`;
    const message = fieldErrors || body?.message || body?.error || fallback;
    throw new ApiError(message, response.status);
  }

  return body;
}

export async function apiGet(path, params) {
  const query = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        query.set(key, value);
      }
    });
  }
  const queryString = query.toString();
  const response = await safeFetch(`${API_BASE_URL}${path}${queryString ? `?${queryString}` : ''}`);
  return handleResponse(response);
}

export async function apiPost(path, body) {
  const response = await safeFetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return handleResponse(response);
}

export async function apiPut(path, body) {
  const response = await safeFetch(`${API_BASE_URL}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return handleResponse(response);
}

export async function apiDelete(path) {
  const response = await safeFetch(`${API_BASE_URL}${path}`, { method: 'DELETE' });
  return handleResponse(response);
}

export async function apiUpload(path, formData) {
  const response = await safeFetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse(response);
}

export function fileUrl(path) {
  return `${API_BASE_URL}${path}`;
}
