// src/components/common/RiskBadge.tsx
// SecureWealth Twin — Risk Level Badge (Admin / Technical Use)
//
// Fixes from original:
//  - Original referenced `stylesForLevel.textColor` and `stylesForLevel.badgeColor`,
//    but RISK_LEVEL_STYLES (theme.ts, Batch 1) only defines `color`, `bgColor`,
//    `label`, and `icon` — those fields don't exist and would render undefined.
//  - Original displayed the raw level string ("LOW", "CRITICAL"). Now displays
//    RISK_LEVEL_STYLES[level].label ("Low Risk", "Critical Risk") and uses the
//    icon already defined per-level in theme.ts, removing a duplicate icon switch.
//
// IMPORTANT — where this component belongs:
// User-facing screens (Dashboard, SecurityReview, TransactionResult, Phishing
// Scanner, Wealth) deliberately do NOT show raw "LOW/MEDIUM/HIGH/CRITICAL"
// risk levels — per the product brief, this confuses non-technical users
// ("LOW" reads as "low security" rather than "you are safe"). Those screens
// use DECISION_STYLES, ZERO_DAY_STYLES, and PHISHING_STYLES instead, which
// frame outcomes in plain language ("Payment Approved", "Looks Safe", etc).
//
// RiskBadge is intended for the Audit Dashboard (admin/bank-officer view,
// Batch 8), where technical risk levels are appropriate and expected.

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, RISK_LEVEL_STYLES, RiskLevel } from '../../constants/theme';

interface RiskBadgeProps {
  level: RiskLevel;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const SIZE_CONFIG = {
  sm: {
    padding: { paddingHorizontal: SPACING.sm, paddingVertical: SPACING.xs },
    radius: BORDER_RADIUS.sm,
    iconSize: 12,
    typography: TYPOGRAPHY.caption,
  },
  md: {
    padding: { paddingHorizontal: SPACING.md, paddingVertical: SPACING.xs },
    radius: BORDER_RADIUS.md,
    iconSize: 14,
    typography: TYPOGRAPHY.bodySm,
  },
  lg: {
    padding: { paddingHorizontal: SPACING.lg, paddingVertical: SPACING.sm },
    radius: BORDER_RADIUS.lg,
    iconSize: 18,
    typography: TYPOGRAPHY.body,
  },
} as const;

const RiskBadge: React.FC<RiskBadgeProps> = ({ level, showIcon = true, size = 'md' }) => {
  const cfg = RISK_LEVEL_STYLES[level];
  const sizeCfg = SIZE_CONFIG[size];

  return (
    <View
      style={[
        styles.container,
        sizeCfg.padding,
        { backgroundColor: cfg.bgColor, borderRadius: sizeCfg.radius },
      ]}
    >
      {showIcon && (
        <Feather
          name={cfg.icon as any}
          size={sizeCfg.iconSize}
          color={cfg.color}
          style={styles.icon}
        />
      )}
      <Text style={[sizeCfg.typography, styles.text, { color: cfg.color }]}>{cfg.label}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'flex-start',
  },
  icon: {
    marginRight: SPACING.xs,
  },
  text: {
    fontWeight: '600',
  },
});

export default RiskBadge;