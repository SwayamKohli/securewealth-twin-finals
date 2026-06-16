// src/components/common/Card.tsx
// SecureWealth Twin — Shared Card Container
//
// Fix from original: SPACING was imported but never used. Now powers an
// optional `padding` prop (default 'lg'), since every card in Batches 2-5
// manually wrote `padding: SPACING.lg` (or similar) into its own styles —
// this lets future screens skip that boilerplate.

import React from 'react';
import { View, ViewStyle, StyleSheet } from 'react-native';
import { COLORS } from '../../constants/colors';
import { SPACING, BORDER_RADIUS, SHADOWS } from '../../constants/theme';

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  variant?: 'default' | 'elevated' | 'outlined';
  radius?: keyof typeof BORDER_RADIUS;
  /** Padding token from SPACING, or 0 for no padding. Default: 'lg' */
  padding?: keyof typeof SPACING | 0;
}

const Card: React.FC<CardProps> = ({
  children,
  style,
  variant = 'default',
  radius = 'lg',
  padding = 'lg',
}) => {
  const paddingValue = padding === 0 ? 0 : SPACING[padding];

  const variantStyle = (() => {
    switch (variant) {
      case 'elevated':
        return styles.elevatedCard;
      case 'outlined':
        return styles.outlinedCard;
      default:
        return styles.defaultCard;
    }
  })();

  return (
    <View
      style={[
        variantStyle,
        { borderRadius: BORDER_RADIUS[radius], padding: paddingValue },
        style,
      ]}
    >
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  defaultCard: {
    backgroundColor: COLORS.surface,
    ...SHADOWS.small,
  },
  elevatedCard: {
    backgroundColor: COLORS.surface,
    ...SHADOWS.medium,
  },
  outlinedCard: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
});

export default Card;