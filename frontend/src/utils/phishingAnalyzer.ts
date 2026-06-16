// src/utils/phishingAnalyzer.ts
// SecureWealth Twin — Mock Phishing Intelligence Engine
//
// Simulates the real Phishing Intelligence Layer (phishing_engine.py).
// Deterministic keyword/pattern matching so the Finals demo reliably
// reproduces all three classifications: SAFE, SUSPICIOUS, PHISHING.
//
// When the real backend is ready, replace `analyzeMessage()` with an API call
// to POST /phishing/scan — the return shape (PhishingAssessment) should match
// what phishing_engine.py + explainability_engine.py output.

export type PhishingClass = 'SAFE' | 'SUSPICIOUS' | 'PHISHING';

export interface PhishingAssessment {
  status: PhishingClass;
  signalIds: string[];
}

// Keyword groups used for pattern matching (lowercase)
const URGENCY_WORDS = ['urgent', 'immediately', 'act now', 'right away', 'within 24 hours', 'expire'];
const THREAT_WORDS = ['suspend', 'block', 'deactivat', 'penalty', 'legal action', 'frozen'];
// Note: these are REQUEST phrases, not just mentions — a message that says
// "do not share this OTP" should NOT match, but "share your OTP" should.
const SENSITIVE_WORDS = [
  'share your otp',
  'share your pin',
  'share your password',
  'enter your otp',
  'enter your pin',
  'enter your cvv',
  'provide your cvv',
  'provide your pin',
  'verify your account',
  'update your kyc',
  'confirm your card',
  'net banking password',
];
const SUSPICIOUS_LINK_PATTERNS = ['.tk', '.xyz', '.info', 'bit.ly', 'tinyurl', 'click here', 'click below', 'click this link'];
const BANK_WORDS = ['bank', 'psb', 'account'];

/**
 * Analyze a message or URL for phishing/scam patterns.
 *
 * Demo rules (deterministic):
 *  1. (Urgency OR Threat) AND (Sensitive request OR Suspicious link)
 *       -> PHISHING
 *  2. Sensitive request OR Urgency OR Threat present alone
 *       -> SUSPICIOUS
 *  3. Otherwise
 *       -> SAFE
 *
 * Bank-related wording combined with any of the above adds the
 * IMPERSONATION signal (since real banks rarely message this way).
 */
export function analyzeMessage(rawText: string): PhishingAssessment {
  const text = rawText.toLowerCase();

  const hasUrgency = URGENCY_WORDS.some((w) => text.includes(w));
  const hasThreat = THREAT_WORDS.some((w) => text.includes(w));
  const hasSensitive = SENSITIVE_WORDS.some((w) => text.includes(w));
  const hasSuspiciousLink = SUSPICIOUS_LINK_PATTERNS.some((w) => text.includes(w));
  const mentionsBank = BANK_WORDS.some((w) => text.includes(w));

  const signalIds: string[] = [];
  if (hasUrgency) signalIds.push('URGENCY');
  if (hasThreat) signalIds.push('THREAT');
  if (hasSensitive) signalIds.push('SENSITIVE_REQUEST');
  if (hasSuspiciousLink) signalIds.push('SUSPICIOUS_LINK');

  const highSeverity = hasUrgency || hasThreat;
  const requestsInfo = hasSensitive || hasSuspiciousLink;

  // Rule 1: PHISHING
  if (highSeverity && requestsInfo) {
    if (mentionsBank) signalIds.push('IMPERSONATION');
    return { status: 'PHISHING', signalIds };
  }

  // Rule 2: SUSPICIOUS
  if (highSeverity || requestsInfo) {
    if (mentionsBank && !signalIds.includes('IMPERSONATION')) signalIds.push('IMPERSONATION');
    return { status: 'SUSPICIOUS', signalIds };
  }

  // Rule 3: SAFE
  return { status: 'SAFE', signalIds: [] };
}