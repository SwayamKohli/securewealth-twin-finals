// src/constants/theme.ts
import { COLORS } from './colors';

// Spacing system (based on 4px grid)
export const SPACING = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
  xxxl: 48,
} as const;

// Typography system
export const TYPOGRAPHY = {
  h1: {
    fontSize: 28,
    fontWeight: '700' as const,
    lineHeight: 34,
  },
  h2: {
    fontSize: 24,
    fontWeight: '700' as const,
    lineHeight: 30,
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
  body: {
    fontSize: 16,
    fontWeight: '400' as const,
    lineHeight: 22,
  },
  bodySm: {
    fontSize: 14,
    fontWeight: '400' as const,
    lineHeight: 20,
  },
  caption: {
    fontSize: 12,
    fontWeight: '400' as const,
    lineHeight: 16,
  },
  button: {
    fontSize: 16,
    fontWeight: '600' as const,
    lineHeight: 20,
  },
} as const;

// Border radius system
export const BORDER_RADIUS = {
  none: 0,
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  xxl: 24,
  full: 9999,
} as const;

// Shadow system (bank-friendly, subtle)
export const SHADOWS = {
  none: {
    shadowColor: 'transparent',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0,
    shadowRadius: 0,
    elevation: 0,
  },
  small: {
    shadowColor: COLORS.textPrimary,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 2,
    elevation: 1,
  },
  medium: {
    shadowColor: COLORS.textPrimary,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 4,
    elevation: 3,
  },
  large: {
    shadowColor: COLORS.textPrimary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.16,
    shadowRadius: 8,
    elevation: 6,
  },
} as const;

// Risk level styles
export const RISK_LEVEL_STYLES = {
  LOW: {
    badgeColor: COLORS.riskLow,
    textColor: COLORS.text,
    bgColor: COLORS.riskLow + '20', // 20% opacity
  },
  MEDIUM: {
    badgeColor: COLORS.riskMedium,
    textColor: COLORS.text,
    bgColor: COLORS.riskMedium + '20',
  },
  HIGH: {
    badgeColor: COLORS.riskHigh,
    textColor: COLORS.text,
    bgColor: COLORS.riskHigh + '20',
  },
  CRITICAL: {
    badgeColor: COLORS.riskCritical,
    textColor: COLORS.text,
    bgColor: COLORS.riskCritical + '20',
  },
} as const;

// Export types for TypeScript
export type TextStyle = React.ComponentProps<typeof import('react-native').Text>['style'];
export type ViewStyle = React.ComponentProps<typeof import('react-native').View>['style'];
export type ButtonStyle = React.ComponentProps<typeof import('react-native').TouchableOpacity>['style'];