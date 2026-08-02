// src/api/deviceSession.ts
// ─────────────────────────────────────────────────────────────────────────────
// Device identity for adaptive security.
//
// WHY THIS EXISTS
//   The backend risk engine scores DEVICE TRUST on every investment: a trusted,
//   long-lived device lowers risk; an unrecognised one raises it and can trigger
//   a step-up challenge (task 4.4).
//
//   Until now the app never registered a device, so the backend always fell back
//   to "NEW_DEVICE / no registered device" — the entire device-trust dimension
//   was running blind. This module fixes that: after login the app registers
//   this physical device once, remembers its id, and reuses it every session.
//
// The device id is persisted locally so the SAME device is recognised across
// app restarts — which is exactly what makes "trusted device" meaningful.
// ─────────────────────────────────────────────────────────────────────────────

import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

import { api } from './apiService';
import type { DeviceResponse } from './types';

const DEVICE_ID_KEY = '@securewealth/device_id';
const DEVICE_NAME_KEY = '@securewealth/device_name';

let cachedDeviceId: string | null = null;

/** Human-readable name for this device, e.g. "iPhone · SecureWealth". */
function buildDeviceName(): string {
  const os = Platform.OS === 'ios' ? 'iPhone' : Platform.OS === 'android' ? 'Android' : 'Device';
  const version = Platform.Version ? ` ${Platform.Version}` : '';
  return `${os}${version}`;
}

/** Maps the running platform to the backend's DeviceType enum. */
function deviceType(): 'IOS' | 'ANDROID' | 'TABLET' | 'LAPTOP' {
  if (Platform.OS === 'ios') return 'IOS';
  if (Platform.OS === 'android') return 'ANDROID';
  return 'LAPTOP';
}

export async function getStoredDeviceId(): Promise<string | null> {
  if (cachedDeviceId) return cachedDeviceId;
  try {
    cachedDeviceId = await AsyncStorage.getItem(DEVICE_ID_KEY);
    return cachedDeviceId;
  } catch {
    return null;
  }
}

export async function getStoredDeviceName(): Promise<string> {
  try {
    return (await AsyncStorage.getItem(DEVICE_NAME_KEY)) || buildDeviceName();
  } catch {
    return buildDeviceName();
  }
}

/**
 * Ensure this device is registered with the backend.
 *
 * Called once after every successful login. Safe to call repeatedly: if the
 * device is already known to the server it is reused rather than duplicated.
 * Never throws — a registration failure must not block the customer from
 * banking; the backend simply treats the session as an unknown device and
 * applies stricter checks, which is the correct fail-safe direction.
 */
export async function ensureDeviceRegistered(): Promise<DeviceResponse | null> {
  try {
    // 1. Already registered on this install?
    const storedId = await getStoredDeviceId();
    if (storedId) {
      const devices = await api.getDevices();
      const match = devices.find((d) => d.device_id === storedId);
      if (match) return match;
      // Stored id no longer exists server-side (e.g. database reseeded) —
      // fall through and register again.
    }

    // 2. Does the server already know a device with this name? Reuse it so a
    //    reinstall doesn't spawn duplicates.
    const name = buildDeviceName();
    const existing = await api.getDevices().catch(() => [] as DeviceResponse[]);
    const sameName = existing.find((d) => d.device_name === name && d.is_active);
    if (sameName) {
      await persist(sameName);
      return sameName;
    }

    // 3. Register it.
    const registered = await api.registerDevice({
      device_name: name,
      device_type: deviceType(),
    });
    await persist(registered);
    return registered;
  } catch {
    // Fail-safe: no device identity => backend treats this as an unknown
    // device and applies stricter verification. Never block login.
    return null;
  }
}

async function persist(device: DeviceResponse): Promise<void> {
  cachedDeviceId = device.device_id;
  try {
    await AsyncStorage.multiSet([
      [DEVICE_ID_KEY, device.device_id],
      [DEVICE_NAME_KEY, device.device_name],
    ]);
  } catch {
    // In-memory cache still serves this session.
  }
}

/** Clear device identity — used on logout only if the user asks to forget it. */
export async function forgetDevice(): Promise<void> {
  cachedDeviceId = null;
  try {
    await AsyncStorage.multiRemove([DEVICE_ID_KEY, DEVICE_NAME_KEY]);
  } catch {
    /* ignore */
  }
}

/** Plain-language description of what a trust status means to a customer. */
export function describeTrust(status: string): { label: string; detail: string } {
  switch (String(status).toUpperCase()) {
    case 'TRUSTED':
      return {
        label: 'Trusted device',
        detail: 'We recognise this device, so most investments go through without extra checks.',
      };
    case 'PENDING':
      return {
        label: 'Being verified',
        detail: 'This device is new. We may ask you to verify a few investments before trusting it.',
      };
    case 'UNTRUSTED':
      return {
        label: 'Not trusted',
        detail: 'Investments from this device will always need extra verification.',
      };
    default:
      return { label: String(status), detail: '' };
  }
}
