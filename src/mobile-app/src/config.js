import Constants from 'expo-constants';

/**
 * Base URL of the REST API, e.g. "http://192.168.0.23/api".
 *
 * The phone cannot reach "localhost" of the PC, so the address is resolved in this order:
 *   1. EXPO_PUBLIC_API_URL from .env (e.g. tunnel mode, or a backend on another machine)
 *   2. the PC's Wi-Fi address that Expo Go already uses to load the app (hostUri, dev only)
 * The API is called through nginx on port 80 ("/api"), like the web UI; port 8081 of the
 * REST API is not used because the Expo dev server would clash with it.
 */
function resolveApiBaseUrl() {
  const fromEnv = process.env.EXPO_PUBLIC_API_URL;
  if (fromEnv) {
    return fromEnv.replace(/\/+$/, '');
  }

  // hostUri looks like "192.168.0.23:8082" (host and port of the Expo dev server)
  const host = Constants.expoConfig?.hostUri?.split(':')[0];
  return host ? `http://${host}/api` : 'http://localhost/api';
}

export const API_BASE_URL = resolveApiBaseUrl();
