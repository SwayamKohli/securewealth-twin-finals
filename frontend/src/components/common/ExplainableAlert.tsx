// src/components/common/ExplainableAlert.tsx
// SecureWealth Twin -- Explainable Alert
//
// Changes from original:
//  - COLORS.s_danger renamed to COLORS.danger throughout (s_danger is the
//    internal alias for PSB.danger, same color -- using the more readable name).
//  - COLORS.warning renamed to COLORS.caution to match Batch 1 color system
//    (COLORS.warning still exists but caution is the semantic name used
//    consistently across all Batch 2-5 screens).
//  - Added `marginVertical` to container style from the original but removed
//    it as a hard-coded value -- callers control vertical spacing via `style`
//    prop instead, matching how every other component in this codebase works.
//  - Alert now shows the full explanation by default when `showExplanation`
//    is true (preserved from original).

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS } from '../../constants/theme';
import Card from './Card';

type AlertType = 'info' | 'success' | 'warning' | 'danger';

interface ExplainableAlertProps {
  type: AlertType;
  title: string;
  explanation: string;
  showExplanation?: boolean;
  onAction?: () => void;
  actionText?: string;
  style?: object;
}

// Map AlertType -> semantic COLORS keys (Batch 1 color system)
const TYPE_CONFIG: Record<AlertType, { color: string; bg: string; icon: string }> = {
  info: {
    color: COLORS.info,
    bg: COLORS.info + '12',
    icon: 'info',
  },
  success: {
    color: COLORS.success,
    bg: COLORS.success + '12',
    icon: 'check-circle',
  },
  warning: {
    // 'warning' AlertType -> COLORS.caution (amber) not COLORS.warning
    // (they are the same value, but caution is the canonical name in this project)
    color: COLORS.caution,
    bg: COLORS.cautionLight,
    icon: 'alert-triangle',
  },
  danger: {
    // Original used COLORS.s_danger -- COLORS.danger is the same value, cleaner name
    color: COLORS.danger,
    bg: COLORS.dangerLight,
    icon: 'alert-octagon',
  },
};

const ExplainableAlert: React.FC<ExplainableAlertProps> = ({
  type,
  title,
  explanation,
  showExplanation = false,
  onAction,
  actionText,
  style,
}) => {
  const [expanded, setExpanded] = useState(showExplanation);
  const cfg = TYPE_CONFIG[type];

  return (
    <Card
      variant="outlined"
      style={StyleSheet.flatten([
        styles.container,
        { borderLeftColor: cfg.color, backgroundColor: cfg.bg },
        style,
      ])}
      padding={0}
    >
      {/* Always-visible header row */}
      <TouchableOpacity
        style={styles.header}
        onPress={() => setExpanded(!expanded)}
        activeOpacity={0.7}
      >
        <Feather name={cfg.icon as any} size={18} color={cfg.color} />
        <Text style={[styles.title, { color: cfg.color }]}>{title}</Text>
        <Feather
          name={expanded ? 'chevron-up' : 'chevron-down'}
          size={18}
          color={cfg.color}
        />
      </TouchableOpacity>

      {/* Expandable explanation */}
      {expanded && (
        <View style={styles.body}>
          <Text style={styles.explanation}>{explanation}</Text>
          {actionText && onAction && (
            <TouchableOpacity style={styles.actionBtn} onPress={onAction} activeOpacity={0.8}>
              <Text style={styles.actionText}>{actionText}</Text>
            </TouchableOpacity>
          )}
        </View>
      )}
    </Card>
  );
};

const styles = StyleSheet.create({
  container: {
    borderLeftWidth: 4,
    // No hard-coded marginVertical -- callers use style prop
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.md,
  },
  title: {
    ...TYPOGRAPHY.bodySmMedium,
    fontWeight: '600',
    flex: 1,
  },
  body: {
    paddingHorizontal: SPACING.md,
    paddingBottom: SPACING.md,
  },
  explanation: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    lineHeight: 20,
  },
  actionBtn: {
    marginTop: SPACING.sm,
    alignSelf: 'flex-start',
    backgroundColor: COLORS.primary,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderRadius: BORDER_RADIUS.md,
  },
  actionText: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textOnDark,
    fontWeight: '600',
  },
});

export default ExplainableAlert;