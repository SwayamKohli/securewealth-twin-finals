// src/constants/colors.ts
export const PSB = {
  // Official Punjab & Sind Bank colors
  green: '#006837',     // Primary (logo green)
  darkGreen: '#004D2D', // Header/drawer
  mediumGreen: '#005A30', // Card headers
  lightGreen: '#E8F5E9', // Light green for highlights

  // Rich gold accent (bank-standard, better contrast than #FFD700)
  gold: '#D4AF37',      // Used for balances, alerts, CTAs

  // Red for alerts/danger
  red: '#C62828',       // PSB red for danger/threats

  // Professional banking backgrounds
  background: '#F5F9FA', // Soft light gray-blue (like SBI/PSB apps)
  cardSurface: '#FFFFFF', // Clean white cards
  cardSurfaceLight: '#F8FAFC', // Lighter card backgrounds

  // Text colors (no pure black for readability)
  textPrimary: '#1F2937',    // Dark gray for primary text
  textSecondary: '#4B5563',  // Medium gray for secondary text
  textTertiary: '#6B7280',   // Lighter gray for tertiary text
  textOnDark: '#FFFFFF',     // White text on dark backgrounds

  // Border colors
  border: '#E5E7EB',         // Light gray borders
  borderDark: '#D1D5DB',     // Darker gray borders

  // Risk level colors (bank-friendly)
  riskLow: '#10B981',        // Emerald (low risk)
  riskMedium: '#F59E0B',     // Amber (medium risk)
  riskHigh: '#EF4444',       // Red (high risk)
  riskCritical: '#DC2626',   // Dark red (critical)

  // Status colors
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  info: '#3B82F6',
} as const;

export const COLORS = {
  // Primary banking colors
  primary: PSB.green,
  primaryDark: PSB.darkGreen,
  primaryMedium: PSB.mediumGreen,
  primaryLight: PSB.lightGreen,
  accent: PSB.gold,
  danger: PSB.red,

  // Backgrounds
  background: PSB.background,
  surface: PSB.cardSurface,
  surfaceLight: PSB.cardSurfaceLight,

  // Text
  text: PSB.textPrimary,
  textSecondary: PSB.textSecondary,
  textTertiary: PSB.textTertiary,
  textOnDark: PSB.textOnDark,

  // Risk levels
  riskLow: PSB.riskLow,
  riskMedium: PSB.riskMedium,
  riskHigh: PSB.riskHigh,
  riskCritical: PSB.riskCritical,

  // Status
  success: PSB.success,
  warning: PSB.warning,
  s_danger: PSB.danger,
  info: PSB.info,

  // Borders
  border: PSB.border,
  borderDark: PSB.borderDark,
} as const;

export default COLORS;