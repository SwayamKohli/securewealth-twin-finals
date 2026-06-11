// src/components/common/Button.tsx
import React from 'react';
import { TouchableOpacity, Text, StyleSheet, ViewStyle, TextStyle } from 'react-native';
import { COLORS, TYPOGRAPHY, BORDER_RADIUS, SPACING } from '../../constants/theme';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
  titleStyle?: TextStyle;
}

const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  style,
  titleStyle,
}) => {
  const getBg = (): string => {
    if (disabled) return COLORS.disabled;
    switch (variant) {
      case 'primary': return COLORS.primary;
      case 'secondary': return COLORS.primaryDark;
      case 'danger': return COLORS.danger;
      case 'outline': return 'transparent';
      default: return COLORS.primary;
    }
  };

  const getBorder = (): string => (variant === 'outline' ? COLORS.primary : 'transparent');
  const getTextColor = (): string => {
    if (variant === 'outline' && !disabled) return COLORS.primary;
    return COLORS.surface;
  };

  const getSize = (): ViewStyle => {
    switch (size) {
      case 'sm': return { paddingHorizontal: 12, paddingVertical: 8 };
      case 'lg': return { paddingHorizontal: 24, paddingVertical: 16 };
      default: return { paddingHorizontal: 16, paddingVertical: 12 };
    }
  };

  return (
    <TouchableOpacity
      style={[
        styles.button,
        {
          backgroundColor: getBg(),
          borderColor: getBorder(),
          borderWidth: variant === 'outline' ? 1 : 0,
          opacity: disabled ? 0.6 : 1,
        },
        getSize(),
        style,
      ]}
      onPress={onPress}
      disabled={loading || disabled}
    >
      {loading ? (
        <Text style={[styles.loadingText, { color: getTextColor() }]}>Loading...</Text>
      ) : (
        <Text
          style={[
            styles.title,
            { color: getTextColor() },
            TYPOGRAPHY.body,
            titleStyle,
          ]}
        >
          {title}
        </Text>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    borderRadius: BORDER_RADIUS.md,
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 80,
    flexDirection: 'row',
  },
  title: {
    fontWeight: '600' as const,
  },
  loadingText: {
    fontWeight: '600' as const,
  },
});

export default Button;