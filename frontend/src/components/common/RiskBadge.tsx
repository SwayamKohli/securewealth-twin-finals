// src/components/common/RiskBadge.tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS } from '../../constants/theme';
import { RISK_LEVEL_STYLES } from '../../constants/theme';

type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

interface RiskBadgeProps {
  level: RiskLevel;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const RiskBadge: React.FC<RiskBadgeProps> = ({ 
  level, 
  showIcon = true, 
  size = 'md' 
}) => {
  const stylesForLevel = RISK_LEVEL_STYLES[level];
  
  const sizeStyle = {
    paddingHorizontal: size === 'sm' ? SPACING.sm : size === 'lg' ? SPACING.lg : SPACING.md,
    paddingVertical: size === 'sm' ? SPACING.xs : size === 'lg' ? SPACING.md : SPACING.sm,
    borderRadius: size === 'sm' ? BORDER_RADIUS.sm : size === 'lg' ? BORDER_RADIUS.lg : BORDER_RADIUS.md,
  };

  const textStyle = {
    ...TYPOGRAPHY[size === 'sm' ? 'caption' : size === 'lg' ? 'body' : 'bodySm'],
    fontWeight: '600' as const,
    color: stylesForLevel.textColor,
  };

  const getIcon = () => {
    switch (level) {
      case 'LOW': return 'check-circle';
      case 'MEDIUM': return 'alert-circle';
      case 'HIGH': return 'alert-triangle';
      case 'CRITICAL': return 'x-circle';
      default: return 'circle';
    }
  };

  return (
    <View 
      style={[
        styles.container,
        { backgroundColor: stylesForLevel.bgColor },
        sizeStyle,
      ]}
    >
      {showIcon && (
        <Feather 
          name={getIcon() as any} 
          size={size === 'sm' ? 12 : size === 'lg' ? 18 : 14} 
          color={stylesForLevel.badgeColor}
          style={{ marginRight: SPACING.xs }}
        />
      )}
      <Text style={textStyle}>{level}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
});

export default RiskBadge;