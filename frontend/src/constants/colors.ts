// src/constants/colors.ts
// SecureWealth Twin — Punjab & Sind Bank Color System
// Design principle: Green = safe/banking, Gold = wealth/growth, Red = danger/fraud

export const PSB = {
  // ── Brand Core ──────────────────────────────────────────────
  green: '#006837',       // Primary PSB brand green (logo)
  darkGreen: '#004D2D',   // Header, bottom tab active bg
  mediumGreen: '#005A30', // Card headers, pressed states
  lightGreen: '#E8F5E9',  // Chip backgrounds, highlight strips
  veryLightGreen: '#F0FAF4', // Page section backgrounds

  // ── Wealth Accent ────────────────────────────────────────────
  gold: '#D4AF37',        // Balance amounts, CTA highlights
  goldLight: '#FDF8E7',   // Gold-tinted card backgrounds
  goldDark: '#B8962E',    // Pressed gold state

  // ── Danger / Fraud ───────────────────────────────────────────
  red: '#C62828',         // Blocked transactions, critical alerts
  redLight: '#FFEBEE',    // Red-tinted card backgrounds
  redMedium: '#EF5350',   // Warning icons

  // ── Amber / Caution ─────────────────────────────────────────
  amber: '#F59E0B',       // WARN state, caution indicators
  amberLight: '#FFFBEB',  // Amber-tinted backgrounds

  // ── Neutral Backgrounds ──────────────────────────────────────
  background: '#F5F9FA',     // Main app background (soft blue-gray)
  cardSurface: '#FFFFFF',    // Standard white cards
  cardSurfaceLight: '#F8FAFC', // Slightly off-white for nested cards
  divider: '#F1F5F9',        // Section dividers

  // ── Text ─────────────────────────────────────────────────────
  textPrimary: '#1F2937',    // Main body text
  textSecondary: '#4B5563',  // Supporting text
  textTertiary: '#9CA3AF',   // Placeholders, hints
  textOnDark: '#FFFFFF',     // White text on green/dark backgrounds
  textOnDarkSub: '#A7F3D0',  // Muted white on dark (e.g. sub-labels on green)
  textGold: '#D4AF37',       // Balance/wealth numbers

  // ── Border ───────────────────────────────────────────────────
  border: '#E5E7EB',
  borderDark: '#D1D5DB',

  // ── Risk Signal Colors ────────────────────────────────────────
  riskLow: '#10B981',        // All clear (emerald)
  riskMedium: '#F59E0B',     // Caution (amber)
  riskHigh: '#EF4444',       // High risk (red)
  riskCritical: '#DC2626',   // Critical (dark red)

  // ── Transaction Decision Colors ───────────────────────────────
  allow: '#10B981',          // ALLOW → green
  warn: '#F59E0B',           // WARN → amber
  challenge: '#6366F1',      // CHALLENGE → indigo (verification)
  block: '#DC2626',          // BLOCK → dark red

  // ── Standard Status ──────────────────────────────────────────
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  info: '#3B82F6',

  // ── Overlay ──────────────────────────────────────────────────
  overlay: 'rgba(0,0,0,0.45)',
  overlayLight: 'rgba(0,0,0,0.15)',
} as const;

// Primary export — named semantic aliases
export const COLORS = {
  // Brand
  primary: PSB.green,
  primaryDark: PSB.darkGreen,
  primaryMedium: PSB.mediumGreen,
  primaryLight: PSB.lightGreen,
  primaryVeryLight: PSB.veryLightGreen,

  // Wealth accent
  accent: PSB.gold,
  accentLight: PSB.goldLight,
  accentDark: PSB.goldDark,

  // Danger
  danger: PSB.red,
  dangerLight: PSB.redLight,
  dangerMedium: PSB.redMedium,

  // Caution
  caution: PSB.amber,
  cautionLight: PSB.amberLight,

  // Backgrounds
  background: PSB.background,
  surface: PSB.cardSurface,
  surfaceLight: PSB.cardSurfaceLight,
  divider: PSB.divider,

  // Text
  text: PSB.textPrimary,
  textSecondary: PSB.textSecondary,
  textTertiary: PSB.textTertiary,
  textOnDark: PSB.textOnDark,
  textOnDarkSub: PSB.textOnDarkSub,
  textAccent: PSB.textGold,

  // Borders
  border: PSB.border,
  borderDark: PSB.borderDark,

  // Risk levels
  riskLow: PSB.riskLow,
  riskMedium: PSB.riskMedium,
  riskHigh: PSB.riskHigh,
  riskCritical: PSB.riskCritical,

  // Transaction decisions
  allow: PSB.allow,
  warn: PSB.warn,
  challenge: PSB.challenge,
  block: PSB.block,

  // Status
  success: PSB.success,
  warning: PSB.warning,
  s_danger: PSB.danger,
  info: PSB.info,

  // Overlay
  overlay: PSB.overlay,
  overlayLight: PSB.overlayLight,
} as const;

export default COLORS;