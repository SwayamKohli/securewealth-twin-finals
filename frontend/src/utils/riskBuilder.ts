// src/utils/riskBuilder.ts
// ─────────────────────────────────────────────────────────────────────────────
// Builds the request payloads for the real security decision chain:
//   POST /ai/fraud/evaluate  → POST /security/risk/evaluate → POST /security/decision/make
//
// The backend needs behavioral/device/environment signals that the UI never
// collects. To preserve the demo scenarios from the old riskSimulator, we
// SYNTHESIZE those signals deterministically from (amount, isNewRecipient):
//
//   • round amount (multiple of 10,000) AND >= 40,000
//       → high-fraud story: new device + night owl + fast OTP + round number  (→ BLOCK)
//   • amount >= 25,000
//       → amount spike                                                         (→ WARN)
//   • new recipient AND amount >= 10,000
//       → new recipient / verify                                              (→ CHALLENGE)
//   • otherwise
//       → clean everyday transaction                                          (→ ALLOW)
//
// The BACKEND makes the final call — we only shape plausible inputs. If the
// backend disagrees with the old thresholds, its decision wins (correct behavior).
// ─────────────────────────────────────────────────────────────────────────────

import type {
  FraudEvaluateRequest,
  RiskEvaluateRequest,
  DecisionMakeRequest,
  BehaviorSignals,
  EnvironmentSignals,
  DeviceTrustSignals,
} from '../api/types';

export interface SynthInput {
  amount: number;
  isNewRecipient: boolean;
}

interface SynthProfile {
  behavior: BehaviorSignals;
  environment: EnvironmentSignals;
  deviceTrust: DeviceTrustSignals;
  // Fraud-model numeric hints
  otpTimeSec: number;
  sessionDuration: number;
  txnsLast1h: number;
  txnsLast24h: number;
  hint: 'FRAUD' | 'SPIKE' | 'NEW_RECIPIENT' | 'CLEAN';
}

/** Deterministic synthesis of signals from the little we actually know. */
export function synthesizeProfile({ amount, isNewRecipient }: SynthInput): SynthProfile {
  const isRoundAmount = amount > 0 && amount % 10000 === 0;

  // Scenario 1: fraud pattern (round + high)
  if (isRoundAmount && amount >= 40000) {
    return {
      hint: 'FRAUD',
      behavior: {
        night_owl: true,
        velocity_burst: true,
        amount_spike: true,
        new_recipient: isNewRecipient,
        otp_distress: true,
        otp_relay: true,
        round_number_anomaly: true,
      },
      environment: {
        ip_region: 'Unknown',
        last_login_region: 'Delhi, IN',
        time_since_last_login_ms: 120000,
        network_type: 'CELLULAR',
      },
      deviceTrust: {
        device_status: 'NEW_DEVICE',
        device_confidence: 20,
        device_age_days: 0,
        security_signals: ['NEW_DEVICE', 'SIM_CHANGED'],
      },
      otpTimeSec: 3,       // suspiciously fast
      sessionDuration: 25,
      txnsLast1h: 4,
      txnsLast24h: 9,
    };
  }

  // Scenario 2: amount spike
  if (amount >= 25000) {
    return {
      hint: 'SPIKE',
      behavior: {
        amount_spike: true,
        new_recipient: isNewRecipient,
      },
      environment: {
        ip_region: 'Delhi, IN',
        last_login_region: 'Delhi, IN',
        time_since_last_login_ms: 3600000,
        network_type: 'WIFI',
      },
      deviceTrust: {
        device_status: 'KNOWN_DEVICE',
        device_confidence: 70,
        device_age_days: 120,
        security_signals: [],
      },
      otpTimeSec: 18,
      sessionDuration: 240,
      txnsLast1h: 1,
      txnsLast24h: 3,
    };
  }

  // Scenario 3: new recipient, meaningful amount
  if (isNewRecipient && amount >= 10000) {
    return {
      hint: 'NEW_RECIPIENT',
      behavior: {
        new_recipient: true,
      },
      environment: {
        ip_region: 'Delhi, IN',
        last_login_region: 'Delhi, IN',
        time_since_last_login_ms: 3600000,
        network_type: 'WIFI',
      },
      deviceTrust: {
        device_status: 'KNOWN_DEVICE',
        device_confidence: 75,
        device_age_days: 120,
        security_signals: [],
      },
      otpTimeSec: 20,
      sessionDuration: 300,
      txnsLast1h: 1,
      txnsLast24h: 2,
    };
  }

  // Scenario 4: clean everyday transaction
  return {
    hint: 'CLEAN',
    behavior: {},
    environment: {
      ip_region: 'Delhi, IN',
      last_login_region: 'Delhi, IN',
      time_since_last_login_ms: 3600000,
      network_type: 'WIFI',
    },
    deviceTrust: {
      device_status: 'TRUSTED_DEVICE',
      device_confidence: 95,
      device_age_days: 400,
      security_signals: [],
    },
    otpTimeSec: 22,
    sessionDuration: 320,
    txnsLast1h: 0,
    txnsLast24h: 1,
  };
}

const now = () => new Date();

/** Fraud-evaluate request. IDs default to 'self'/'unknown' if not supplied. */
export function buildFraudRequest(
  input: SynthInput,
  ids: { userId?: string; deviceId?: string; recipientId?: string } = {}
): FraudEvaluateRequest {
  const p = synthesizeProfile(input);
  const d = now();
  return {
    user_id: ids.userId || 'self',
    device_id: ids.deviceId || 'current-device',
    recipient_id: ids.recipientId || 'recipient',
    amount: input.amount,
    hour: d.getHours(),
    day_of_week: d.getDay(),
    otp_time_sec: p.otpTimeSec,
    session_duration: p.sessionDuration,
    txns_last_1h: p.txnsLast1h,
    txns_last_24h: p.txnsLast24h,
  };
}

/** Risk-evaluate request, combining synthesized signals with the AI fraud output. */
export function buildRiskRequest(
  input: SynthInput,
  aiFraudProbability: number,
  aiConfidence: number
): RiskEvaluateRequest {
  const p = synthesizeProfile(input);
  return {
    behavior_signals: p.behavior,
    environment: p.environment,
    device_trust: p.deviceTrust,
    ai_fraud_probability: aiFraudProbability,
    ai_confidence: aiConfidence,
  };
}

/** Decision request — the final call that returns ALLOW/WARN/CHALLENGE/BLOCK. */
export function buildDecisionRequest(
  input: SynthInput,
  args: {
    transactionId: string;
    accountId: string;
    channel: string;
    aiFraudProbability: number;
    aiConfidence: number;
  }
): DecisionMakeRequest {
  const p = synthesizeProfile(input);
  return {
    transaction_id: args.transactionId,
    account_id: args.accountId,
    amount: input.amount,
    channel: args.channel,
    risk_input: {
      behavior_signals: p.behavior,
      environment: p.environment,
      device_trust: p.deviceTrust,
      ai_fraud_probability: args.aiFraudProbability,
      ai_confidence: args.aiConfidence,
    },
  };
}

// Map the backend decision's security_signals / synthesized hint to the signal IDs
// the SecurityReview "What We Checked" section renders (keys in risk_signals.json).
export function signalIdsFor(hint: SynthProfile['hint']): string[] {
  switch (hint) {
    case 'FRAUD':
      return ['NEW_DEVICE', 'NIGHT_OWL', 'FAST_OTP', 'ROUND_NUMBER'];
    case 'SPIKE':
      return ['AMOUNT_SPIKE'];
    case 'NEW_RECIPIENT':
      return ['NEW_RECIPIENT'];
    default:
      return [];
  }
}