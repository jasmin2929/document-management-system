import { API_BASE_URL } from '../config';

// Shown when the REST API cannot be reached at all (backend stopped, wrong Wi-Fi, nginx 502/503/504)
export const SERVER_UNREACHABLE_MESSAGE =
  'The server is not reachable. Check that the backend is running and that your phone is in the same Wi-Fi as the PC.';
export const TIMEOUT_MESSAGE = 'The server did not respond in time. Please try again.';

// Gateway errors come from nginx, not from the REST API, so their body has no useful message
const GATEWAY_ERROR_STATUSES = new Set([502, 503, 504]);

// Mobile networks can hang without ever failing; a timeout turns that into a visible error
const DEFAULT_TIMEOUT_MS = 15_000;
// Uploads may take longer on a slow connection (max. 20 MB)
const UPLOAD_TIMEOUT_MS = 120_000;

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    // 0 = no HTTP response at all (network error or timeout)
    this.status = status;
  }
}

// fetch() only rejects on network errors (it resolves for 4xx/5xx) and has no built-in timeout
async function safeFetch(url, options = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);

  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } catch (error) {
    // the user only sees a friendly message; the original error goes to the Metro terminal for debugging
    console.warn(`[api] ${options.method || 'GET'} ${url} failed${timedOut ? ' (timeout)' : ''}:`, error);
    throw new ApiError(timedOut ? TIMEOUT_MESSAGE : SERVER_UNREACHABLE_MESSAGE, 0);
  } finally {
    clearTimeout(timer);
  }
}

async function handleResponse(response) {
  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get('content-type') || '';
  const body = contentType.includes('application/json') ? await response.json().catch(() => null) : null;

  if (!response.ok) {
    // Error format of the REST API's GlobalExceptionHandler: { status, error, message } or { errors: {field: msg} }
    const fieldErrors = body?.errors ? Object.values(body.errors).join(' ') : null;
    const fallback = GATEWAY_ERROR_STATUSES.has(response.status)
      ? SERVER_UNREACHABLE_MESSAGE
      : `Request failed with status ${response.status}`;
    throw new ApiError(fieldErrors || body?.message || body?.error || fallback, response.status);
  }

  return body;
}

function buildUrl(path, params) {
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, String(value));
    }
  });
  const queryString = query.toString();
  return `${API_BASE_URL}${path}${queryString ? `?${queryString}` : ''}`;
}

export async function apiGet(path, params) {
  return handleResponse(await safeFetch(buildUrl(path, params)));
}

export async function apiPost(path, body) {
  const response = await safeFetch(buildUrl(path), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return handleResponse(response);
}

export async function apiPut(path, body) {
  const response = await safeFetch(buildUrl(path), {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return handleResponse(response);
}

export async function apiDelete(path) {
  return handleResponse(await safeFetch(buildUrl(path), { method: 'DELETE' }));
}

// No Content-Type header: fetch sets "multipart/form-data" including the boundary itself
export async function apiUpload(path, formData) {
  const response = await safeFetch(buildUrl(path), { method: 'POST', body: formData }, UPLOAD_TIMEOUT_MS);
  return handleResponse(response);
}

export function fileUrl(path) {
  return buildUrl(path);
}
