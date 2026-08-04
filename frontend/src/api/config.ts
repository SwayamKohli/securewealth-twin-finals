// src/api/config.ts
// ─────────────────────────────────────────────────────────────────────────────
// Single source of truth for backend connection.
// Change the URL HERE (or via app.config.js `extra.apiBaseUrl`) — nowhere else.
// ─────────────────────────────────────────────────────────────────────────────

// If you later add `expo-constants`, you can replace the line below with:
//   import Constants from 'expo-constants';
//   const fromExtra = Constants.expoConfig?.extra?.apiBaseUrl;
// and fall back to the default.

/**
 * Backend base URL.
 *
 * Since your mobile device and backend server are on the same WiFi network (10.107.1.x),
 * use your computer's IP address to connect to the backend.
 */
export const API_BASE_URL = 'http://10.104.7.97:8000';

// Some endpoints in the API doc are NOT under /api/v1 (e.g. /dashboard/*).
// We keep the raw host separately so those can be called too.
export const API_HOST = API_BASE_URL;

// Request timeout (ms). fetch has no native timeout, so we wrap with AbortController.
// 45s default. This app is not a normal CRUD client: a single call can run the
// behaviour engine, the fraud model, zero-day detection, the risk engine and the
// decision engine, then write a signed audit record. 20s was cutting off work
// the server went on to finish — which left the app showing a failure for an
// investment that had actually completed.
export const REQUEST_TIMEOUT_MS = 45000;

/** Calls that move money or run the full security pipeline. */
export const LONG_TIMEOUT_MS = 90000;