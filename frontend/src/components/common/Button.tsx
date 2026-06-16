// src/components/common/Button.tsx
// SecureWealth Twin — Shared Button
//
// Fixes from original:
//  - COLORS was imported from '../../constants/theme', but theme.ts does not
//    re-export it (it only imports COLORS internally from colors.ts for use
//    in DECISION_STYLES/RISK_LEVEL_STYLES etc). Now imported from colors.ts directly.
//  - COLORS.disabled did not exist anywhere in the color system. Replaced with
//    COLORS.borderDark, matching the disabled-button pattern already used in
//    TransactionInitiateScreen / SecurityReviewScreen (submitBtnDisabled).
//  - Sizes now use SPACING tokens instead of magic numbers.
//  - Added optional `icon` + `iconPosition` props, since almost every button
//    built in Batches 2-5 pairs a Feather icon with text.
//  - Loading state now uses ActivityIndicator instead of a "Loading..." text
//    swap, which shifted button width.

import React from 'react';
import { TouchableOpacity, Text, StyleSheet, ActivityIndicator, ViewStyle, TextStyle } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../../constants/colors';
import { TYPOGRAPHY, BORDER_RADIUS, SPACING } from '../../constants/theme';

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: string;
  iconPosition?: 'left' | 'right';
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  style?: ViewStyle;
  titleStyle?: TextStyle;
}

// Variant -> colors. Each variant defines its enabled AND disabled appearance,
// so disabled state never needs a separate "disabled" color token.
const VARIANT_STYLES: Record<
  ButtonVariant,
  { bg: string; border: string; text: string; bgDisabled: string; borderDisabled: string; textDisabled: string }
> = {
  primary: {
    bg: COLORS.primary,
    border: 'transparent',
    text: COLORS.textOnDark,
    bgDisabled: COLORS.borderDark,
    borderDisabled: 'transparent',
    textDisabled: COLORS.textOnDark,
  },
  secondary: {
    bg: COLORS.primaryDark,
    border: 'transparent',
    text: COLORS.textOnDark,
    bgDisabled: COLORS.borderDark,
    borderDisabled: 'transparent',
    textDisabled: COLORS.textOnDark,
  },
  outline: {
    bg: 'transparent',
    border: COLORS.primary,
    text: COLORS.primary,
    bgDisabled: 'transparent',
    borderDisabled: COLORS.borderDark,
    textDisabled: COLORS.textTertiary,
  },
  danger: {
    bg: COLORS.danger,
    border: 'transparent',
    text: COLORS.textOnDark,
    bgDisabled: COLORS.borderDark,
    borderDisabled: 'transparent',
    textDisabled: COLORS.textOnDark,
  },
  ghost: {
    bg: 'transparent',
    border: 'transparent',
    text: COLORS.primary,
    bgDisabled: 'transparent',
    borderDisabled: 'transparent',
    textDisabled: COLORS.textTertiary,
  },
};

// Size -> padding (SPACING tokens) + typography + icon size
const SIZE_STYLES: Record<ButtonSize, { padding: ViewStyle; typography: TextStyle; iconSize: number }> = {
  sm: {
    padding: { paddingHorizontal: SPACING.md, paddingVertical: SPACING.sm },
    typography: TYPOGRAPHY.buttonSm,
    iconSize: 14,
  },
  md: {
    padding: { paddingHorizontal: SPACING.lg, paddingVertical: SPACING.md },
    typography: TYPOGRAPHY.button,
    iconSize: 16,
  },
  lg: {
    padding: { paddingHorizontal: SPACING.xl, paddingVertical: SPACING.md },
    typography: TYPOGRAPHY.button,
    iconSize: 18,
  },
};

const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'md',
  icon,
  iconPosition = 'left',
  loading = false,
  disabled = false,
  fullWidth = false,
  style,
  titleStyle,
}) => {
  const colors = VARIANT_STYLES[variant];
  const sizeCfg = SIZE_STYLES[size];
  const isDisabled = disabled || loading;

  const bg = isDisabled ? colors.bgDisabled : colors.bg;
  const border = isDisabled ? colors.borderDisabled : colors.border;
  const textColor = isDisabled ? colors.textDisabled : colors.text;

  return (
    <TouchableOpacity
      style={[
        styles.button,
        sizeCfg.padding,
        {
          backgroundColor: bg,
          borderColor: border,
          borderWidth: variant === 'outline' ? 1 : 0,
          width: fullWidth ? '100%' : undefined,
        },
        style,
      ]}
      onPress={onPress}
      disabled={isDisabled}
      activeOpacity={0.8}
    >
      {loading ? (
        <ActivityIndicator size="small" color={textColor} />
      ) : (
        <>
          {icon && iconPosition === 'left' && (
            <Feather name={icon as any} size={sizeCfg.iconSize} color={textColor} style={styles.iconLeft} />
          )}
          <Text style={[sizeCfg.typography, styles.title, { color: textColor }, titleStyle]}>
            {title}
          </Text>
          {icon && iconPosition === 'right' && (
            <Feather name={icon as any} size={sizeCfg.iconSize} color={textColor} style={styles.iconRight} />
          )}
        </>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    borderRadius: BORDER_RADIUS.lg,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
  },
  title: {
    fontWeight: '600',
  },
  iconLeft: {
    marginRight: SPACING.sm,
  },
  iconRight: {
    marginLeft: SPACING.sm,
  },
});

export default Button;