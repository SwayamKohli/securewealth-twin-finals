// src/components/common/GlassCard.tsx
import React from 'react';
import { View, StyleSheet } from 'react-native';
import { COLORS } from '../../constants/colors';

interface GlassCardProps {
  children: React.ReactNode;
  radius?: number;
  style?: any;
}

const GlassCard: React.FC<GlassCardProps> = ({ children, radius = 16, style }) => {
  return (
    <View style={[styles.container, { borderRadius: radius }, style]}>
      {/* Subtle frosted overlay — no blur, no artifacts */}
      <View style={styles.overlay} />
      <View style={styles.content}>
        {children}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    overflow: 'hidden',
    backgroundColor: 'rgba(255, 255, 255, 0.7)', // Slightly more opaque than before
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.04)',
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 16,
  },
  content: {
    padding: 16,
  },
});

export default GlassCard;