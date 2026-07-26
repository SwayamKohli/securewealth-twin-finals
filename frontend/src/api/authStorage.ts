// src/api/authStorage.ts
// ─────────────────────────────────────────────────────────────────────────────
// JWT token persistence. Uses AsyncStorage (already in package.json).
// Swap the 3 storage calls for expo-secure-store later if you want hardware-backed
// storage — the rest of the app only touches these functions, never storage directly.
// ─────────────────────────────────────────────────────────────────────────────

import AsyncStorage from '@react-native-async-storage/async-storage';

const TOKEN_KEY = '@securewealth/jwt';

// In-memory cache so apiService can attach the header synchronously after login,
// without awaiting AsyncStorage on every request.
let cachedToken: string | null = null;

export async function saveToken(token: string): Promise<void> {
  cachedToken = token;
  try {
    await AsyncStorage.setItem(TOKEN_KEY, token);
  } catch (e) {
    // Non-fatal: token still works this session via the in-memory cache.
    console.warn('[authStorage] Failed to persist token:', e);
  }
}

export async function loadToken(): Promise<string | null> {
  if (cachedToken) return cachedToken;
  try {
    const t = await AsyncStorage.getItem(TOKEN_KEY);
    cachedToken = t;
    return t;
  } catch (e) {
    console.warn('[authStorage] Failed to load token:', e);
    return null;
  }
}

/** Synchronous accessor — returns null until loadToken()/saveToken() has run once. */
export function getCachedToken(): string | null {
  return cachedToken;
}

export async function clearToken(): Promise<void> {
  cachedToken = null;
  try {
    await AsyncStorage.removeItem(TOKEN_KEY);
  } catch (e) {
    console.warn('[authStorage] Failed to clear token:', e);
  }
}

export async function isLoggedIn(): Promise<boolean> {
  const t = await loadToken();
  return !!t;
}