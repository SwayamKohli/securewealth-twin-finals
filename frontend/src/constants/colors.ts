// src/constants/colors.ts
export const PSB = {
  // Official Punjab & Sind Bank colors
  green: '#006837',     // Primary (logo)
  darkGreen: '#004D2D', // Header/drawer
  mediumGreen: '#005A30',
  lightGreen: '#E8F5E9',

  // Rich gold (bank-standard) — NOT too light
  gold: '#D4AF37',      // Better contrast than #FFD700

  // Red for alerts
  red: '#C62828',

  // Backgrounds — balanced, professional
  background: '#F5F9FA',   // Light gray-blue (SBI-style)
  cardSurface: '#FFFFFF',

  // Text — high contrast on background
  darkGray: '#1F2937',    // Primary text
  mediumGray: '#4B5563',  // Secondary
  lightGray: '#9CA3AF',   // Tertiary
};

export const COLORS = {
  primary: PSB.green,
  primaryDark: PSB.darkGreen,
  primaryMedium: PSB.mediumGreen,
  primaryLight: PSB.lightGreen,
  accent: PSB.gold,        // ✅ Richer gold
  danger: PSB.red,
  success: '#10B981',
  warning: '#F59E0B',

  background: PSB.background,
  surface: PSB.cardSurface,
  cardSurface: PSB.cardSurface,

  text: PSB.darkGray,
  textSecondary: PSB.mediumGray,
  textTertiary: PSB.lightGray,
  textOnDark: '#FFFFFF',

  border: '#E5E7EB',
} as const;

export default COLORS;