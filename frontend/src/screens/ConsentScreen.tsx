// src/screens/ConsentScreen.tsx
// ─────────────────────────────────────────────────────────────────────────────
// Account Aggregation consent gate (task 2.1).
//
// The backend enforces consent: every aggregated endpoint sits behind
// `require_aa_consent` and returns 403 without it. Until now the app never
// asked, so a fresh customer hit an unexplained error with no way out.
//
// This screen is that way out. It is rendered INLINE by the Wealth tab when
// consent is missing — no navigation detour, and the moment consent is granted
// the same screen reloads with real data.
//
// Written to RBI Account Aggregator expectations: state plainly what is
// accessed, why, for how long, and make withdrawal obviously available.
// ─────────────────────────────────────────────────────────────────────────────

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Feather } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import { api } from '../api/apiService';
import { useI18n } from '../i18n';

type Props = {
  /** Called after consent is successfully granted, so the caller can reload. */
  onGranted: () => void;
};

const WE_ACCESS = [
  {
    icon: 'credit-card',
    title: 'Account balances',
    detail: 'Balances and account types across the banks you choose to link.',
  },
  {
    icon: 'trending-up',
    title: 'Deposits and investments',
    detail: 'Fixed and recurring deposits so we can show your true net worth.',
  },
  {
    icon: 'activity',
    title: 'Income and spending summary',
    detail: 'Monthly totals only — used to judge what you can safely invest.',
  },
];

const WE_NEVER = [
  'Move money or place investments on your behalf',
  'Share your data with anyone outside Punjab & Sind Bank',
  'Keep your data after you withdraw consent',
];

const ConsentScreen = ({ onGranted }: Props) => {
  const { t } = useI18n();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const grant = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await api.grantConsent();
      onGranted();
    } catch {
      setError('We could not record your consent. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.heroIcon}>
        <Feather name="shield" size={28} color={COLORS.primary} />
      </View>
      <Text style={styles.title}>{t('consent.title')}</Text>
      <Text style={styles.subtitle}>{t('consent.subtitle')}</Text>

      <Text style={styles.sectionLabel}>{t('consent.weAccess')}</Text>
      <View style={styles.card}>
        {WE_ACCESS.map((item, i) => (
          <View
            key={item.title}
            style={[styles.accessRow, i === WE_ACCESS.length - 1 && styles.rowLast]}
          >
            <View style={styles.accessIcon}>
              <Feather name={item.icon as any} size={15} color={COLORS.primary} />
            </View>
            <View style={styles.flex1}>
              <Text style={styles.accessTitle}>{item.title}</Text>
              <Text style={styles.accessDetail}>{item.detail}</Text>
            </View>
          </View>
        ))}
      </View>

      <Text style={styles.sectionLabel}>{t('consent.weNever')}</Text>
      <View style={styles.card}>
        {WE_NEVER.map((line) => (
          <View key={line} style={styles.neverRow}>
            <Feather name="x-circle" size={14} color={COLORS.danger} />
            <Text style={styles.neverText}>{line}</Text>
          </View>
        ))}
      </View>

      <View style={styles.noteBox}>
        <Feather name="info" size={14} color={COLORS.primaryDark} />
        <Text style={styles.noteText}>
          Read-only access. Your consent is recorded with a timestamp and stays in
          the tamper-protected audit trail, so there is always a record of what you
          agreed to and when.
        </Text>
      </View>

      {error ? (
        <View style={styles.errorBox}>
          <Feather name="alert-triangle" size={14} color={COLORS.danger} />
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : null}

      <TouchableOpacity
        style={[styles.primaryBtn, submitting && styles.btnDisabled]}
        onPress={grant}
        disabled={submitting}
        activeOpacity={0.85}
      >
        {submitting ? (
          <ActivityIndicator color={COLORS.textOnDark} />
        ) : (
          <>
            <Feather name="check" size={16} color={COLORS.textOnDark} />
            <Text style={styles.primaryBtnText}>{t('consent.agree')}</Text>
          </>
        )}
      </TouchableOpacity>

      <Text style={styles.footer}>{t('consent.footer')}</Text>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: SPACING.lg, paddingBottom: SPACING.xxl },
  flex1: { flex: 1 },

  heroIcon: {
    width: 60, height: 60, borderRadius: 18, alignSelf: 'center',
    backgroundColor: COLORS.primaryVeryLight,
    alignItems: 'center', justifyContent: 'center', marginBottom: SPACING.md,
  },
  title: { ...TYPOGRAPHY.h2, color: COLORS.text, textAlign: 'center' },
  subtitle: {
    ...TYPOGRAPHY.body, color: COLORS.textSecondary, textAlign: 'center',
    lineHeight: 21, marginTop: SPACING.sm, marginBottom: SPACING.xl,
  },

  sectionLabel: {
    ...TYPOGRAPHY.captionBold, color: COLORS.textSecondary,
    textTransform: 'uppercase', letterSpacing: 0.7, marginBottom: SPACING.sm,
  },
  card: {
    backgroundColor: COLORS.surface, borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1, borderColor: COLORS.border,
    padding: SPACING.md, marginBottom: SPACING.lg,
  },

  accessRow: {
    flexDirection: 'row', gap: SPACING.md, paddingVertical: SPACING.sm,
    borderBottomWidth: 1, borderBottomColor: COLORS.divider,
  },
  rowLast: { borderBottomWidth: 0 },
  accessIcon: {
    width: 32, height: 32, borderRadius: 9,
    backgroundColor: COLORS.primaryVeryLight,
    alignItems: 'center', justifyContent: 'center',
  },
  accessTitle: { ...TYPOGRAPHY.bodyMedium, color: COLORS.text },
  accessDetail: {
    ...TYPOGRAPHY.caption, color: COLORS.textTertiary,
    marginTop: 2, lineHeight: 16,
  },

  neverRow: {
    flexDirection: 'row', alignItems: 'flex-start',
    gap: SPACING.sm, paddingVertical: 5,
  },
  neverText: { ...TYPOGRAPHY.body, color: COLORS.textSecondary, flex: 1, lineHeight: 19 },

  noteBox: {
    flexDirection: 'row', gap: SPACING.sm,
    backgroundColor: COLORS.primaryVeryLight, borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md, marginBottom: SPACING.lg,
  },
  noteText: {
    ...TYPOGRAPHY.caption, color: COLORS.primaryDark,
    flex: 1, lineHeight: 17,
  },

  errorBox: {
    flexDirection: 'row', alignItems: 'center', gap: SPACING.sm,
    backgroundColor: COLORS.dangerLight, borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md, marginBottom: SPACING.md,
  },
  errorText: { ...TYPOGRAPHY.caption, color: COLORS.danger, flex: 1 },

  primaryBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: SPACING.sm, backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.lg, paddingVertical: SPACING.md, ...SHADOWS.medium,
  },
  btnDisabled: { opacity: 0.6 },
  primaryBtnText: { ...TYPOGRAPHY.bodyMedium, color: COLORS.textOnDark, fontWeight: '700' },

  footer: {
    ...TYPOGRAPHY.caption, color: COLORS.textTertiary,
    textAlign: 'center', marginTop: SPACING.md, lineHeight: 16,
  },
});

export default ConsentScreen;
