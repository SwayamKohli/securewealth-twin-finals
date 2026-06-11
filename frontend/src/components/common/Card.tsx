// src/components/common/Card.tsx
import React from 'react';
import { View, StyleSheet } from 'react-native';
import { COLORS } from '../../constants/colors';
import { SPACING, BORDER_RADIUS, SHADOWS } from '../../constants/theme';

interface CardProps {
  children: React.ReactNode;
  style?: any;
  variant?: 'default' | 'elevated' | 'outlined';
  radius?: keyof typeof BORDER_RADIUS;
}

const Card: React.FC<CardProps> = ({ 
  children, 
  style, 
  variant = 'default',
  radius = 'lg',
}) => {
  const getStyle = () => {
    switch (variant) {
      case 'elevated':
        return [styles.elevatedCard, { borderRadius: BORDER_RADIUS[radius] }];
      case 'outlined':
        return [styles.outlinedCard, { borderRadius: BORDER_RADIUS[radius] }];
      default:
        return [styles.defaultCard, { borderRadius: BORDER_RADIUS[radius] }];
    }
  };

  return (
    <View style={[getStyle(), style]}>
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