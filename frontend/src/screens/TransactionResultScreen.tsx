// src/screens/TransactionResultScreen.tsx
// SecureWealth Twin — Payment Receipt
//
// BACKEND INTEGRATION (minimal):
//  • If SecurityReview initiated a real transaction, its transaction_id is used
//    as the Reference ID. Otherwise we fall back to a generated PSB reference,
//    so the screen still works if no real txn was created.
//  • Everything else (copy, layout, navigation) is unchanged.
//
// Receives { transactionData, assessment }. assessment.transactionId may be set.

import React, { useRef } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { COLORS } from '../constants/colors';
import { useI18n } from '../i18n';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS, DECISION_STYLES } from '../constants/theme';
import { generateReferenceId } from '../utils/riskSimulator';

// ── Helpers ───────────────────────────────────────────────────────────────────
const formatCurrency = (n: number) => '\u20B9' + n.toLocaleString('en-IN');

const formatDateTime = (iso: string) =>
  new Date(iso).toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  });

// Decision -> receipt copy (distinct from SecurityReview's DECISION_STYLES titles,
// since this screen frames everything as "completed", not "in review")
const RECEIPT_COPY: Record<string, { title: string; subtitle: string }> = {
  ALLOW: {
    title: 'Payment Successful',
    subtitle: 'Your money is on its way.',
  },
  WARN: {
    title: 'Payment Sent',
    subtitle: 'Your payment went through. We flagged it for your awareness — no action needed.',
  },
  CHALLENGE: {
    title: 'Payment Verified & Sent',
    subtitle: 'Thanks for confirming — your money is on its way.',
  },
  BLOCK: {
    title: 'Payment Stopped',
    subtitle: 'This payment did not go through. Your account is safe.',
  },
};

// ── Sub-components ────────────────────────────────────────────────────────────
const DetailRow = ({
  label,
  value,
  emphasize,
}: {
  label: string;
  value: string;
  emphasize?: boolean;
}) => (
  <View style={styles.detailRow}>
    <Text style={styles.detailLabel}>{label}</Text>
    <Text style={[styles.detailValue, emphasize && styles.detailValueEmphasis]} numberOfLines={1}>
      {value}
    </Text>
  </View>
);

// ── Main Screen ───────────────────────────────────────────────────────────────
const TransactionResultScreen = ({ route, navigation }: any) => {
  const { t } = useI18n();
  const { transactionData, assessment } = route.params;
  const insets = useSafeAreaInsets();

  // Reference ID: prefer the real backend transaction_id, else a generated one.
  const generatedRef = useRef(generateReferenceId()).current;
  const referenceId = assessment?.transactionId || generatedRef;
  const completedAt = useRef(new Date().toISOString()).current;

  const decision = assessment.decision as 'ALLOW' | 'WARN' | 'CHALLENGE' | 'BLOCK';
  const decisionStyle = DECISION_STYLES[decision];
  const receipt = RECEIPT_COPY[decision];

  const isSuccess = decision !== 'BLOCK';

  // ── Navigation actions ──────────────────────────────────────────────────────
  const handleDone = () => {
    navigation.popToTop();
    navigation.getParent()?.navigate('HomeTab');
  };

  const handleSendAnother = () => {
    navigation.popToTop();
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
    >
      {/* Status header */}
      <View style={styles.statusHeader}>
        <View
          style={[
            styles.statusIconWrap,
            { backgroundColor: decisionStyle.bgColor, borderColor: decisionStyle.borderColor },
          ]}
        >
          <Feather name={isSuccess ? 'check' : 'x'} size={44} color={decisionStyle.color} />
        </View>
        <Text style={[styles.statusTitle, { color: decisionStyle.color }]}>{receipt.title}</Text>
        <Text style={styles.statusSubtitle}>{receipt.subtitle}</Text>

        {isSuccess && (
          <Text style={styles.amountDisplay}>{formatCurrency(transactionData.amount)}</Text>
        )}
      </View>

      {/* Receipt card */}
      <View style={styles.card}>
        <View style={styles.cardHeaderRow}>
          <Text style={styles.cardTitle}>{t('result.paymentDetails')}</Text>
          <View style={[styles.statusBadge, { backgroundColor: decisionStyle.bgColor }]}>
            <Text style={[styles.statusBadgeText, { color: decisionStyle.color }]}>
              {isSuccess ? 'Completed' : 'Stopped'}
            </Text>
          </View>
        </View>

        <DetailRow label={t('result.reference')} value={referenceId} emphasize />
        <DetailRow label={t('result.amount')} value={formatCurrency(transactionData.amount)} />
        <DetailRow
          label="To"
          value={`${transactionData.toLabel} \u00B7 ${transactionData.toDetail}`}
        />
        <DetailRow
          label="From"
          value={`${transactionData.fromAccount.bankName} ${transactionData.fromAccount.masked}`}
        />
        <DetailRow label={t('result.mode')} value={transactionData.paymentMode} />
        <DetailRow label={t('result.dateTime')} value={formatDateTime(completedAt)} />
        {transactionData.note ? <DetailRow label="Note" value={transactionData.note} /> : null}
      </View>

      {/* Trust footer */}
      <View style={styles.trustFooter}>
        <Feather name="shield" size={16} color={COLORS.success} />
        <Text style={styles.trustFooterText}>
          {isSuccess
            ? 'Your money is protected. A permanent record of this has been saved to your account.'
            : 'Your account is safe. We have saved a permanent record of this and our team has been alerted.'}
        </Text>
      </View>

      {/* Actions */}
      <View style={styles.actions}>
        <TouchableOpacity style={styles.primaryBtn} onPress={handleDone} activeOpacity={0.8}>
          <Feather name="home" size={16} color={COLORS.textOnDark} />
          <Text style={styles.primaryBtnText}>Done</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.secondaryBtn}
          onPress={handleSendAnother}
          activeOpacity={0.8}
        >
          <Feather name="repeat" size={16} color={COLORS.primary} />
          <Text style={styles.secondaryBtnText}>{t('result.another')}</Text>
        </TouchableOpacity>
      </View>

      <View style={{ height: insets.bottom + SPACING.xl }} />
    </ScrollView>
  );
};

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollContent: {
    padding: SPACING.lg,
  },

  statusHeader: {
    alignItems: 'center',
    paddingTop: SPACING.xl,
    paddingBottom: SPACING.lg,
  },
  statusIconWrap: {
    width: 96,
    height: 96,
    borderRadius: BORDER_RADIUS.full,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1.5,
    marginBottom: SPACING.lg,
  },
  statusTitle: {
    ...TYPOGRAPHY.h2,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: SPACING.xs,
  },
  statusSubtitle: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    textAlign: 'center',
    paddingHorizontal: SPACING.lg,
    marginBottom: SPACING.md,
  },
  amountDisplay: {
    ...TYPOGRAPHY.display,
    color: COLORS.text,
    fontWeight: '700',
    marginTop: SPACING.sm,
  },

  card: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    marginBottom: SPACING.md,
    ...SHADOWS.small,
  },
  cardHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  cardTitle: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.text,
    fontWeight: '700',
  },
  statusBadge: {
    borderRadius: BORDER_RADIUS.full,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 3,
  },
  statusBadgeText: {
    ...TYPOGRAPHY.captionBold,
  },

  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: SPACING.xs,
    borderTopWidth: 1,
    borderTopColor: COLORS.divider,
  },
  detailLabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textTertiary,
  },
  detailValue: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.text,
    fontWeight: '600',
    flexShrink: 1,
    marginLeft: SPACING.md,
    textAlign: 'right',
  },
  detailValueEmphasis: {
    color: COLORS.primary,
    fontWeight: '700',
  },

  trustFooter: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: SPACING.sm,
    backgroundColor: COLORS.primaryVeryLight,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
  },
  trustFooterText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.primaryMedium,
    flex: 1,
    lineHeight: 19,
  },

  actions: {
    gap: SPACING.sm,
  },
  primaryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.lg,
    paddingVertical: SPACING.md,
    gap: SPACING.sm,
  },
  primaryBtnText: {
    ...TYPOGRAPHY.button,
    color: COLORS.textOnDark,
  },
  secondaryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    paddingVertical: SPACING.md,
    gap: SPACING.sm,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  secondaryBtnText: {
    ...TYPOGRAPHY.button,
    color: COLORS.primary,
  },
});

export default TransactionResultScreen;