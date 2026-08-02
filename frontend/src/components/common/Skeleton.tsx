// src/components/common/Skeleton.tsx
// ─────────────────────────────────────────────────────────────────────────────
// Skeleton placeholders (M7, task 19).
//
// A centred spinner tells the customer "something is happening" and nothing
// else. A skeleton tells them what is about to arrive and roughly how much of
// it — the screen stops jumping when data lands, and a slow network feels like
// loading rather than breakage.
//
// It matters more here than in most apps: the Wealth tab opens on a net-worth
// figure. A blank screen followed by a sudden number reads as instability in a
// banking app. The shape appearing first, then filling, reads as steady.
//
// Uses the native driver so the shimmer keeps running smoothly while the JS
// thread is busy parsing the API response.
// ─────────────────────────────────────────────────────────────────────────────

import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated, Easing, type ViewStyle } from 'react-native';

import { COLORS } from '../../constants/colors';
import { SPACING, BORDER_RADIUS } from '../../constants/theme';

/** One shimmering block. Width may be a number or a percentage string. */
export const SkeletonBlock = ({
  width = '100%',
  height = 14,
  radius = BORDER_RADIUS.sm,
  style,
}: {
  width?: number | string;
  height?: number;
  radius?: number;
  style?: ViewStyle;
}) => {
  const pulse = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, {
          toValue: 1,
          duration: 750,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulse, {
          toValue: 0,
          duration: 750,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [pulse]);

  const opacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.45, 0.9] });

  return (
    <Animated.View
      style={[
        {
          width: width as any,
          height,
          borderRadius: radius,
          backgroundColor: COLORS.border,
          opacity,
        },
        style,
      ]}
      // Invisible to screen readers: it is decoration, and announcing
      // "placeholder" repeatedly is worse than announcing nothing.
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    />
  );
};

/** Card-shaped placeholder: a title line plus body lines. */
export const SkeletonCard = ({
  lines = 3,
  showAvatar = false,
}: {
  lines?: number;
  showAvatar?: boolean;
}) => (
  <View style={styles.card}>
    <View style={styles.row}>
      {showAvatar && <SkeletonBlock width={40} height={40} radius={BORDER_RADIUS.full} />}
      <View style={styles.flex1}>
        <SkeletonBlock width="55%" height={13} />
        <SkeletonBlock width="35%" height={10} style={{ marginTop: 6 }} />
      </View>
    </View>
    {Array.from({ length: lines }).map((_, i) => (
      <SkeletonBlock
        key={i}
        width={i === lines - 1 ? '70%' : '100%'}
        height={10}
        style={{ marginTop: SPACING.sm }}
      />
    ))}
  </View>
);

/** Wealth tab: hero figure, then the cards below it. */
export const WealthSkeleton = () => (
  <View style={styles.screen}>
    <View style={styles.hero}>
      <SkeletonBlock width={110} height={12} />
      <SkeletonBlock width={190} height={30} style={{ marginTop: SPACING.md }} />
      <View style={[styles.row, { marginTop: SPACING.lg }]}>
        <SkeletonBlock width="46%" height={44} radius={BORDER_RADIUS.md} />
        <SkeletonBlock width="46%" height={44} radius={BORDER_RADIUS.md} />
      </View>
    </View>
    <View style={styles.body}>
      <SkeletonCard lines={2} />
      <SkeletonCard lines={3} />
      <SkeletonCard lines={2} />
    </View>
  </View>
);

/** Dashboard: account card carousel, then the list beneath. */
export const DashboardSkeleton = () => (
  <View style={styles.screen}>
    <View style={styles.body}>
      <SkeletonBlock width="100%" height={168} radius={BORDER_RADIUS.xl} />
      <SkeletonCard lines={3} />
      <SkeletonBlock width="45%" height={13} style={{ marginTop: SPACING.lg }} />
      {[0, 1, 2].map((i) => (
        <View key={i} style={[styles.row, { marginTop: SPACING.md }]}>
          <SkeletonBlock width={38} height={38} radius={BORDER_RADIUS.full} />
          <View style={styles.flex1}>
            <SkeletonBlock width="60%" height={12} />
            <SkeletonBlock width="35%" height={10} style={{ marginTop: 6 }} />
          </View>
          <SkeletonBlock width={64} height={14} />
        </View>
      ))}
    </View>
  </View>
);

/** Security activity: a day header plus grouped rows. */
export const ActivitySkeleton = () => (
  <View style={styles.body}>
    <SkeletonBlock width="100%" height={56} radius={BORDER_RADIUS.lg} />
    <SkeletonBlock width={70} height={11} style={{ marginTop: SPACING.lg }} />
    {[0, 1, 2, 3].map((i) => (
      <View key={i} style={{ marginTop: SPACING.sm }}>
        <SkeletonCard lines={1} showAvatar />
      </View>
    ))}
  </View>
);

/** Profile: identity header plus the section cards. */
export const ProfileSkeleton = () => (
  <View style={[styles.body, { alignItems: 'center' }]}>
    <SkeletonBlock width={72} height={72} radius={BORDER_RADIUS.full} />
    <SkeletonBlock width={150} height={18} style={{ marginTop: SPACING.md }} />
    <SkeletonBlock width={110} height={20} radius={BORDER_RADIUS.full} style={{ marginTop: SPACING.xs }} />
    <View style={{ width: '100%', marginTop: SPACING.xl }}>
      <SkeletonCard lines={3} />
      <SkeletonCard lines={2} showAvatar />
    </View>
  </View>
);

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background },
  hero: { backgroundColor: COLORS.primaryDark, padding: SPACING.lg, paddingBottom: SPACING.xl },
  body: { padding: SPACING.lg, backgroundColor: COLORS.background, flex: 1 },
  flex1: { flex: 1 },
  row: { flexDirection: 'row', alignItems: 'center', gap: SPACING.md },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: SPACING.md,
    marginTop: SPACING.md,
  },
});

export default SkeletonBlock;
