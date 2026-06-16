// SecureWealth Twin — Mock Risk Decision Engine
//
// This simulates what the real Security & Risk Layer (FastAPI backend) will do.
// Logic is deterministic so the Finals demo reproduces the blueprint's scenarios:
//   Flow 1 (Safe Transaction)    → ALLOW
//   Flow 2 (Fraud Attempt)       → BLOCK  (new device + night owl + fast OTP + round number)
//
// When the real backend is ready, replace `assessTransaction()` with an API call
// to POST /transaction/evaluate — the return shape (RiskAssessment) should match
// what the backend's decision_engine.py outputs.

export type Decision = 'ALLOW' | 'WARN' | 'CHALLENGE' | 'BLOCK';
export type ZeroDayClass = 'KNOWN' | 'SUSPICIOUS' | 'UNKNOWN';

export interface RiskAssessment {
  decision: Decision;
  riskScore: number;
  zeroDayClass: ZeroDayClass;
  signalIds: string[];
}

interface AssessInput {
  amount: number;
  isNewRecipient: boolean;
}

/**
 * Assess a transaction and return a decision + supporting signals.
 *
 * Demo rules (deterministic, no randomness — important for live demos):
 *  1. Round amount (multiple of ₹10,000) AND >= ₹40,000
 *     → BLOCK  (mirrors blueprint Flow 2: new device + night owl + fast OTP + round number)
 *  2. Amount >= ₹25,000
 *     → WARN   (amount spike relative to typical spending)
 *  3. New recipient AND amount >= ₹10,000
 *     → CHALLENGE (verify it's really the user)
 *  4. Otherwise
 *     → ALLOW  (normal, everyday transaction)
 */
export function assessTransaction({ amount, isNewRecipient }: AssessInput): RiskAssessment {
  const isRoundAmount = amount > 0 && amount % 10000 === 0;

  // Rule 1: Fraud-pattern demo (round + high amount)
  if (isRoundAmount && amount >= 40000) {
    return {
      decision: 'BLOCK',
      riskScore: 92,
      zeroDayClass: 'UNKNOWN',
      signalIds: ['NEW_DEVICE', 'NIGHT_OWL', 'FAST_OTP', 'ROUND_NUMBER'],
    };
  }

  // Rule 2: Amount spike
  if (amount >= 25000) {
    return {
      decision: 'WARN',
      riskScore: 38,
      zeroDayClass: 'SUSPICIOUS',
      signalIds: ['AMOUNT_SPIKE'],
    };
  }

  // Rule 3: New recipient, meaningful amount
  if (isNewRecipient && amount >= 10000) {
    return {
      decision: 'CHALLENGE',
      riskScore: 55,
      zeroDayClass: 'SUSPICIOUS',
      signalIds: ['NEW_RECIPIENT'],
    };
  }

  // Rule 4: Everyday transaction
  return {
    decision: 'ALLOW',
    riskScore: 8,
    zeroDayClass: 'KNOWN',
    signalIds: [],
  };
}

/**
 * Generate a mock reference ID for completed transactions.
 * Format mirrors typical bank reference numbers: PSB + date + random digits
 */
export function generateReferenceId(): string {
  const now = new Date();
  const datePart =
    now.getFullYear().toString().slice(2) +
    String(now.getMonth() + 1).padStart(2, '0') +
    String(now.getDate()).padStart(2, '0');
  const randomPart = Math.floor(100000 + Math.random() * 900000);
  return `PSB${datePart}${randomPart}`;
}