// src/screens/SafetyHubScreen.tsx
// SecureWealth Twin — Safety Hub (root of Safety tab)
//
// Landing page with two action cards:
//   1. Check a Message or Link -> PhishingScannerScreen
//   2. My Security Activity    -> MySecurityActivityScreen
//
// Plus a short "Good to Know" reassurance section with general account-safety
// tips (kept distinct from the Phishing Scanner's message-specific warning
// signs, to avoid duplicating content between the two screens).

import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Feather } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';

// General account-safety reminders (not phishing-specific — see PhishingScannerScreen
// for message-analysis warning signs)
const SAFETY_TIPS = [
  {
    icon: 'eye',
    text: 'We watch every transaction for unusual activity, 24 hours a day.',
  },
  {
    icon: 'message-circle',
    text: "If we ever flag something, we'll always explain why in plain language.",
  },
  {
    icon: 'shield',
    text: 'Never share your MPIN, OTP, or password with anyone -- not even bank staff.',
  },
];

// ── Sub-components ────────────────────────────────────────────────────────────

// Big tappable action card
const ActionCard = ({
  icon,
  iconColor,
  iconBg,
  title,
  description,
  badge,
  onPress,
}: {
  icon: string;
  iconColor: string;
  iconBg: string;
  title: string;
  description: string;
  badge?: string;
  onPress: () => void;
}) => (
  <TouchableOpacity style={styles.actionCard} onPress={onPress} activeOpacity={0.7}>
    <View style={[styles.actionIconWrap, { backgroundColor: iconBg }]}>
      <Feather name={icon as any} size={24} color={iconColor} />
    </View>
    <View style={styles.actionTextWrap}>
      <View style={styles.actionTitleRow}>
        <Text style={styles.actionTitle}>{title}</Text>
        {badge && (
          <View style={styles.badge}>
            <Text style={styles.badgeText}>{badge}</Text>
          </View>
        )}
      </View>
      <Text style={styles.actionDescription}>{description}</Text>
    </View>
    <Feather name="chevron-right" size={20} color={COLORS.textTertiary} />
  </TouchableOpacity>
);

// ── Main Screen ───────────────────────────────────────────────────────────────
const SafetyHubScreen = ({ navigation }: any) => {
  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Hero */}
      <View style={styles.hero}>
        <View style={styles.heroIconWrap}>
          <Feather name="shield" size={32} color={COLORS.success} />
        </View>
        <Text style={styles.heroTitle}>Stay Protected</Text>
        <Text style={styles.heroSubtitle}>
          We're always watching for fraud and scams -- here's how you can stay one step
          ahead too.
        </Text>
      </View>

      {/* Content */}
      <View style={styles.content}>
        {/* Action cards */}
        <View style={styles.section}>
          <ActionCard
            icon="message-square"
            iconColor={COLORS.primary}
            iconBg={COLORS.primaryVeryLight}
            title="Check a Message or Link"
            description="Got a text, email, or WhatsApp message that feels off? Paste it here and we'll check it for warning signs."
            onPress={() => navigation.navigate('PhishingScanner')}
          />
          <ActionCard
            icon="activity"
            iconColor={COLORS.accentDark}
            iconBg={COLORS.accentLight}
            title="My Security Activity"
            description="See a plain-English history of security checks and alerts on your account."
            onPress={() => navigation.navigate('MySecurityActivity')}
          />
        </View>

        <View style={styles.sectionDivider} />

        {/* Good to know */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Good to Know</Text>
          {SAFETY_TIPS.map((tip, i) => (
            <View key={i} style={styles.tipRow}>
              <View style={styles.tipIconWrap}>
                <Feather name={tip.icon as any} size={16} color={COLORS.primary} />
              </View>
              <Text style={styles.tipText}>{tip.text}</Text>
            </View>
          ))}
        </View>

        <View style={{ height: SPACING.xxl }} />
      </View>
    </ScrollView>
  );
};

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.primaryDark,
  },

  hero: {
    backgroundColor: COLORS.primaryDark,
    alignItems: 'center',
    paddingHorizontal: SPACING.xl,
    paddingTop: SPACING.lg,
    paddingBottom: SPACING.xxl,
  },
  heroIconWrap: {
    width: 64,
    height: 64,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: 'rgba(255,255,255,0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  heroTitle: {
    ...TYPOGRAPHY.h2,
    color: COLORS.textOnDark,
    fontWeight: '700',
    marginBottom: SPACING.xs,
  },
  heroSubtitle: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textOnDarkSub,
    textAlign: 'center',
    lineHeight: 20,
  },

  content: {
    backgroundColor: COLORS.background,
    borderTopLeftRadius: BORDER_RADIUS.xxxl,
    borderTopRightRadius: BORDER_RADIUS.xxxl,
    marginTop: -BORDER_RADIUS.xl,
    paddingTop: SPACING.xl,
  },
  sectionDivider: {
    height: SPACING.xs,
    backgroundColor: COLORS.divider,
  },
  section: {
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.lg,
  },
  sectionTitle: {
    ...TYPOGRAPHY.h4,
    color: COLORS.text,
    fontWeight: '700',
    marginBottom: SPACING.md,
  },

  actionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    marginBottom: SPACING.md,
    gap: SPACING.md,
    ...SHADOWS.small,
  },
  actionIconWrap: {
    width: 48,
    height: 48,
    borderRadius: BORDER_RADIUS.lg,
    justifyContent: 'center',
    alignItems: 'center',
    flexShrink: 0,
  },
  actionTextWrap: {
    flex: 1,
  },
  actionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginBottom: 2,
  },
  actionTitle: {
    ...TYPOGRAPHY.bodyMedium,
    color: COLORS.text,
    fontWeight: '700',
  },
  badge: {
    backgroundColor: COLORS.accentLight,
    borderRadius: BORDER_RADIUS.full,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 1,
  },
  badgeText: {
    ...TYPOGRAPHY.captionBold,
    color: COLORS.accentDark,
  },
  actionDescription: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    lineHeight: 19,
  },

  tipRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: SPACING.md,
    marginBottom: SPACING.md,
  },
  tipIconWrap: {
    width: 32,
    height: 32,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.primaryVeryLight,
    justifyContent: 'center',
    alignItems: 'center',
    flexShrink: 0,
  },
  tipText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    flex: 1,
    lineHeight: 20,
    paddingTop: 6,
  },
});

export default SafetyHubScreen;