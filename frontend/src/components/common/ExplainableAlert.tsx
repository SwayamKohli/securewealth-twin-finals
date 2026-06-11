// src/components/common/ExplainableAlert.tsx
import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import Card from './Card';
import { COLORS } from '../../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS } from '../../constants/theme';

type AlertType = 'info' | 'success' | 'warning' | 'danger';

interface ExplainableAlertProps {
  type: AlertType;
  title: string;
  explanation: string;
  showExplanation?: boolean;
  onAction?: () => void;
  actionText?: string;
}

const ExplainableAlert: React.FC<ExplainableAlertProps> = ({
  type,
  title,
  explanation,
  showExplanation = false,
  onAction,
  actionText,
}) => {
  const [expanded, setExpanded] = useState(showExplanation);

  const getColor = () => {
    switch (type) {
      case 'info': return COLORS.info;
      case 'success': return COLORS.success;
      case 'warning': return COLORS.warning;
      case 'danger': return COLORS.s_danger;
      default: return COLORS.text;
    }
  };

  const getIcon = () => {
    switch (type) {
      case 'info': return 'info';
      case 'success': return 'check-circle';
      case 'warning': return 'alert-triangle';
      case 'danger': return 'alert-octagon';
      default: return 'info';
    }
  };

  const getBackgroundColor = () => {
    switch (type) {
      case 'info': return COLORS.info + '10';
      case 'success': return COLORS.success + '10';
      case 'warning': return COLORS.warning + '10';
      case 'danger': return COLORS.s_danger + '10';
      default: return COLORS.text + '10';
    }
  };

  return (
    <Card style={[styles.container, { borderLeftColor: getColor(), backgroundColor: getBackgroundColor() }]}>
      <View style={styles.header}>
        <View style={styles.iconContainer}>
          <Feather name={getIcon() as any} size={20} color={getColor()} />
        </View>
        <Text style={[styles.title, { color: getColor() }]}>{title}</Text>
        <TouchableOpacity onPress={() => setExpanded(!expanded)} style={styles.expandButton}>
          <Feather name={expanded ? 'chevron-up' : 'chevron-down'} size={20} color={getColor()} />
        </TouchableOpacity>
      </View>
      
      {expanded && (
        <View style={styles.explanationContainer}>
          <Text style={styles.explanation}>{explanation}</Text>
          {actionText && onAction && (
            <TouchableOpacity style={styles.actionButton} onPress={onAction}>
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
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    marginVertical: SPACING.sm,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconContainer: {
    marginRight: SPACING.sm,
  },
  title: {
    ...TYPOGRAPHY.bodySm,
    fontWeight: '600',
    flex: 1,
  },
  expandButton: {
    padding: SPACING.xs,
  },
  explanationContainer: {
    marginTop: SPACING.sm,
  },
  explanation: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    lineHeight: 20,
  },
  actionButton: {
    marginTop: SPACING.sm,
    alignSelf: 'flex-start',
    backgroundColor: COLORS.primary,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderRadius: BORDER_RADIUS.sm,
  },
  actionText: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textOnDark,
    fontWeight: '600',
  },
});

export default ExplainableAlert;