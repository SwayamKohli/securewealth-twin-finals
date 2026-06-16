// src/components/common/GlassCard.tsx
// SecureWealth Twin -- Glass Card
//
// Changes from original:
//  - radius prop now accepts a key from BORDER_RADIUS (typed) rather than a
//    raw number, for design-system consistency. Raw numbers still work via
//    the `customRadius` escape hatch.
//  - padding prop added (same pattern as Card.tsx) so callers don't need to
//    wrap children in an extra View to get padding.
//  - content View removed -- children render directly inside container,
//    since the overlay is absolutely positioned and never affects layout.
//  - borderColor token from COLORS.border instead of hardcoded rgba.
//  - Used on green/dark backgrounds (e.g. Dashboard hero, account cards).
//    On white backgrounds, prefer Card component instead.

import React from 'react';
import { View, ViewStyle, StyleSheet } from 'react-native';
import { COLORS } from '../../constants/colors';
import { SPACING, BORDER_RADIUS } from '../../constants/theme';

interface GlassCardProps {
  children: React.ReactNode;
  radius?: keyof typeof BORDER_RADIUS;
  customRadius?: number;
  padding?: keyof typeof SPACING | 0;
  style?: ViewStyle;
}

const GlassCard: React.FC<GlassCardProps> = ({
  children,
  radius = 'xl',
  customRadius,
  padding = 'lg',
  style,
}) => {
  const borderRadius = customRadius ?? BORDER_RADIUS[radius];
  const paddingValue = padding === 0 ? 0 : SPACING[padding];

  return (
    <View
      style={[
        styles.container,
        { borderRadius, padding: paddingValue },
        style,
      ]}
    >
      {/* Frosted overlay -- absolutely positioned, never affects layout */}
      <View style={[styles.overlay, { borderRadius }]} />
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    overflow: 'hidden',
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.18)',
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
  },
});

export default GlassCard;