// src/constants/theme.ts
// SecureWealth Twin — Design Token System

import { COLORS } from './colors';

// ── Spacing (4px grid) ───────────────────────────────────────────────────────
export const SPACING = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
  xxxl: 48,
} as const;

// ── Typography ───────────────────────────────────────────────────────────────
// Designed for banking: large, legible, clear hierarchy
export const TYPOGRAPHY = {
  // Display — balance amounts, hero numbers
  display: {
    fontSize: 36,
    fontWeight: '700' as const,
    lineHeight: 42,
    letterSpacing: -0.5,
  },
  // Page titles
  h1: {
    fontSize: 28,
    fontWeight: '700' as const,
    lineHeight: 34,
    letterSpacing: -0.3,
  },
  h2: {
    fontSize: 24,
    fontWeight: '700' as const,
    lineHeight: 30,
    letterSpacing: -0.2,
  },
  h3: {
    fontSize: 20,
    fontWeight: '600' as const,
    lineHeight: 26,
  },
  h4: {
    fontSize: 18,
    fontWeight: '600' as const,
    lineHeight: 24,
  },
  // Body text
  body: {
    fontSize: 16,
    fontWeight: '400' as const,
    lineHeight: 22,
  },
  bodyMedium: {
    fontSize: 16,
    fontWeight: '500' as const,
    lineHeight: 22,
  },
  bodySm: {
    fontSize: 14,
    fontWeight: '400' as const,
    lineHeight: 20,
  },
  bodySmMedium: {
    fontSize: 14,
    fontWeight: '500' as const,
    lineHeight: 20,
  },
  // Labels & captions
  label: {
    fontSize: 13,
    fontWeight: '500' as const,
    lineHeight: 18,
    letterSpacing: 0.1,
  },
  caption: {
    fontSize: 12,
    fontWeight: '400' as const,
    lineHeight: 16,
  },
  captionBold: {
    fontSize: 12,
    fontWeight: '600' as const,
    lineHeight: 16,
    letterSpacing: 0.2,
  },
  // Buttons
  button: {
    fontSize: 16,
    fontWeight: '600' as const,
    lineHeight: 20,
  },
  buttonSm: {
    fontSize: 14,
    fontWeight: '600' as const,
    lineHeight: 18,
  },
  // Overline — section labels like "YOUR ACCOUNTS"
  overline: {
    fontSize: 11,
    fontWeight: '700' as const,
    lineHeight: 14,
    letterSpacing: 1.2,
    textTransform: 'uppercase' as const,
  },
} as const;

// ── Border Radius ────────────────────────────────────────────────────────────
export const BORDER_RADIUS = {
  none: 0,
  xs: 4,
  sm: 6,
  md: 10,
  lg: 14,
  xl: 18,
  xxl: 24,
  xxxl: 32,
  full: 9999,
} as const;

// ── Shadows ──────────────────────────────────────────────────────────────────
// Using a dark neutral, not COLORS.text directly, to avoid type issues
export const SHADOWS = {
  none: {
    shadowColor: 'transparent',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0,
    shadowRadius: 0,
    elevation: 0,
  },
  xs: {
    shadowColor: '#1F2937',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  small: {
    shadowColor: '#1F2937',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 3,
    elevation: 2,
  },
  medium: {
    shadowColor: '#1F2937',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 6,
    elevation: 4,
  },
  large: {
    shadowColor: '#1F2937',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.16,
    shadowRadius: 10,
    elevation: 8,
  },
  card: {
    shadowColor: '#006837',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
} as const;

// ── Risk Level Styles ────────────────────────────────────────────────────────
// Maps internal risk levels to display colors
export const RISK_LEVEL_STYLES = {
  LOW: {
    color: COLORS.riskLow,
    bgColor: COLORS.riskLow + '18',
    label: 'Low Risk',
    icon: 'shield' as const,
  },
  MEDIUM: {
    color: COLORS.riskMedium,
    bgColor: COLORS.riskMedium + '18',
    label: 'Medium Risk',
    icon: 'alert-triangle' as const,
  },
  HIGH: {
    color: COLORS.riskHigh,
    bgColor: COLORS.riskHigh + '18',
    label: 'High Risk',
    icon: 'alert-circle' as const,
  },
  CRITICAL: {
    color: COLORS.riskCritical,
    bgColor: COLORS.riskCritical + '18',
    label: 'Critical Risk',
    icon: 'x-circle' as const,
  },
} as const;

// ── Transaction Decision Styles ──────────────────────────────────────────────
// Maps ALLOW / WARN / CHALLENGE / BLOCK to user-friendly display
export const DECISION_STYLES = {
  ALLOW: {
    color: COLORS.allow,
    bgColor: COLORS.allow + '15',
    borderColor: COLORS.allow + '40',
    // What the user sees:
    title: 'Payment Approved',
    subtitle: 'Your transaction is safe and complete.',
    icon: 'check-circle' as const,
  },
  WARN: {
    color: COLORS.warn,
    bgColor: COLORS.warn + '15',
    borderColor: COLORS.warn + '40',
    title: 'We Noticed Something Unusual',
    subtitle: 'Your payment went through, but please review the details below.',
    icon: 'alert-triangle' as const,
  },
  CHALLENGE: {
    color: COLORS.challenge,
    bgColor: COLORS.challenge + '15',
    borderColor: COLORS.challenge + '40',
    title: 'Please Verify It\'s You',
    subtitle: 'An extra check is needed before this payment can proceed.',
    icon: 'shield' as const,
  },
  BLOCK: {
    color: COLORS.block,
    bgColor: COLORS.block + '12',
    borderColor: COLORS.block + '35',
    title: 'Payment Stopped for Your Safety',
    subtitle: 'We blocked this transaction because it looked suspicious.',
    icon: 'x-circle' as const,
  },
} as const;

// ── Phishing Classification Styles ───────────────────────────────────────────
export const PHISHING_STYLES = {
  SAFE: {
    color: COLORS.success,
    bgColor: COLORS.success + '15',
    label: 'Looks Safe',
    sublabel: 'We did not find anything suspicious.',
    icon: 'check-circle' as const,
  },
  SUSPICIOUS: {
    color: COLORS.caution,
    bgColor: COLORS.caution + '15',
    label: 'Be Careful',
    sublabel: 'This message has some warning signs. Do not share any personal details.',
    icon: 'alert-triangle' as const,
  },
  PHISHING: {
    color: COLORS.danger,
    bgColor: COLORS.dangerLight,
    label: 'This Looks Like a Scam',
    sublabel: 'Do not click any links or share any information from this message.',
    icon: 'alert-octagon' as const,
  },
} as const;

// ── Unknown Risk Classification ───────────────────────────────────────────────
// KNOWN / SUSPICIOUS / UNKNOWN maps for zero-day detector output
export const ZERO_DAY_STYLES = {
  KNOWN: {
    color: COLORS.success,
    bgColor: COLORS.success + '15',
    label: 'Normal Activity',
    sublabel: 'This matches your usual behaviour.',
  },
  SUSPICIOUS: {
    color: COLORS.caution,
    bgColor: COLORS.caution + '15',
    label: 'Looks Unusual',
    sublabel: 'This is different from how you normally transact.',
  },
  UNKNOWN: {
    color: COLORS.danger,
    bgColor: COLORS.dangerLight,
    label: 'Needs Review',
    sublabel: 'We have flagged this for additional verification.',
  },
} as const;

// ── Bottom Tab Bar Constants ─────────────────────────────────────────────────
export const TAB_BAR = {
  height: 64,
  paddingBottom: 8,
  iconSize: 22,
  labelSize: 11,
} as const;

// ── Header Constants ─────────────────────────────────────────────────────────
export const HEADER = {
  height: 56,
  paddingHorizontal: 16,
} as const;

// ── Card Defaults ────────────────────────────────────────────────────────────
export const CARD = {
  padding: 16,
  borderRadius: 14,
  marginBottom: 12,
} as const;

// ── Animation Durations ───────────────────────────────────────────────────────
export const ANIMATION = {
  fast: 150,
  normal: 250,
  slow: 400,
  verySlow: 600,
} as const;

// ── Export types ─────────────────────────────────────────────────────────────
export type RiskLevel = keyof typeof RISK_LEVEL_STYLES;
export type DecisionType = keyof typeof DECISION_STYLES;
export type PhishingResult = keyof typeof PHISHING_STYLES;
export type ZeroDayResult = keyof typeof ZERO_DAY_STYLES;