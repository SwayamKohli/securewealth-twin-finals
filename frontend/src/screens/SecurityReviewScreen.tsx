// src/screens/SecurityReviewScreen.tsx
// SecureWealth Twin — Security Check
//
// Two phases:
//  1. 'checking'  — animated shield + cycling status messages (~1.8s)
//  2. 'result'    — decision-specific UI built from DECISION_STYLES (theme.ts)
//
// Decision-specific actions (CRITICAL — security-first principle from blueprint):
//  ALLOW     -> single "Continue" button
//  WARN      -> "Continue Payment" (primary) + "Cancel and go back" (text link)
//  CHALLENGE -> quick MPIN re-verification, then "Verify & Continue"
//  BLOCK     -> NO continue option at all. Only "Go to Home" + "Report This Was Me".
//               This is intentional: a blocked payment must never be resumable
//               from this screen, matching the blueprint's "Payment Stopped for
//               Your Safety" guarantee.
//
// When the real backend is ready: replace the `assessTransaction()` call with
// POST /transaction/evaluate, and replace the `riskSignalsData` lookup with
// whatever explanation strings the explanation_engine.py returns (same shape
// is recommended: { friendlyName, explanation, icon, severity }).

import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Animated,
  Easing,
  TextInput,
  Alert,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { COLORS } from '../constants/colors';
import {
  SPACING,
  TYPOGRAPHY,
  BORDER_RADIUS,
  SHADOWS,
  DECISION_STYLES,
  ZERO_DAY_STYLES,
} from '../constants/theme';
import { assessTransaction, RiskAssessment } from '../utils/riskSimulator';
import riskSignalsData from '../../mockData/risk_signals.json';

// ── Helpers ───────────────────────────────────────────────────────────────────
const formatCurrency = (n: number) => '\u20B9' + n.toLocaleString('en-IN');

const formatTime = (iso: string) =>
  new Date(iso).toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  });

const signalDefs = riskSignalsData.signalDefinitions as Record<
  string,
  { friendlyName: string; explanation: string; icon: string; severity: string }
>;

// Cycling messages shown during the "checking" phase
const CHECK_STEPS = [
  'Checking your device\u2026',
  'Checking transaction pattern\u2026',
  'Checking recipient details\u2026',
  'Finishing your safety check\u2026',
];

type Phase = 'checking' | 'result';

// ── Sub-components ────────────────────────────────────────────────────────────

// Animated rotating shield shown during the checking phase
const CheckingView = () => {
  const spinAnim = useRef(new Animated.Value(0)).current;
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    Animated.loop(
      Animated.timing(spinAnim, {
        toValue: 1,
        duration: 1400,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();

    const interval = setInterval(() => {
      setStepIndex((i) => (i + 1) % CHECK_STEPS.length);
    }, 450);
    return () => clearInterval(interval);
  }, []);

  const spin = spinAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <View style={styles.checkingContainer}>
      <Animated.View style={[styles.checkingIconWrap, { transform: [{ rotate: spin }] }]}>
        <Feather name="shield" size={56} color={COLORS.primary} />
      </Animated.View>
      <Text style={styles.checkingTitle}>Checking your payment</Text>
      <Text style={styles.checkingStep}>{CHECK_STEPS[stepIndex]}</Text>
      <Text style={styles.checkingHint}>This usually takes just a few seconds</Text>
    </View>
  );
};

// Single transaction detail row
const DetailRow = ({ label, value }: { label: string; value: string }) => (
  <View style={styles.detailRow}>
    <Text style={styles.detailLabel}>{label}</Text>
    <Text style={styles.detailValue} numberOfLines={1}>
      {value}
    </Text>
  </View>
);

// Collapsible "what we checked" signal row
const SignalRow = ({
  signalId,
  expanded,
  onToggle,
}: {
  signalId: string;
  expanded: boolean;
  onToggle: () => void;
}) => {
  const def = signalDefs[signalId];
  if (!def) return null;

  const severityColor = def.severity === 'HIGH' ? COLORS.danger : COLORS.caution;

  return (
    <TouchableOpacity style={styles.signalRow} onPress={onToggle} activeOpacity={0.7}>
      <View style={styles.signalRowHeader}>
        <View style={[styles.signalIconWrap, { backgroundColor: severityColor + '15' }]}>
          <Feather name={def.icon as any} size={16} color={severityColor} />
        </View>
        <Text style={styles.signalName}>{def.friendlyName}</Text>
        <Feather
          name={expanded ? 'chevron-up' : 'chevron-down'}
          size={16}
          color={COLORS.textTertiary}
        />
      </View>
      {expanded && <Text style={styles.signalExplanation}>{def.explanation}</Text>}
    </TouchableOpacity>
  );
};

// ── Main Screen ───────────────────────────────────────────────────────────────
const SecurityReviewScreen = ({ route, navigation }: any) => {
  const { transactionData } = route.params;
  const insets = useSafeAreaInsets();

  const [phase, setPhase] = useState<Phase>('checking');
  const [assessment, setAssessment] = useState<RiskAssessment | null>(null);
  const [expandedSignal, setExpandedSignal] = useState<string | null>(null);
  const [mpin, setMpin] = useState('');

  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(16)).current;

  useEffect(() => {
    const timer = setTimeout(() => {
      const result = assessTransaction({
        amount: transactionData.amount,
        isNewRecipient: transactionData.isNewRecipient,
      });
      setAssessment(result);
      setPhase('result');

      Animated.parallel([
        Animated.timing(fadeAnim, { toValue: 1, duration: 350, useNativeDriver: true }),
        Animated.timing(slideAnim, {
          toValue: 0,
          duration: 350,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }),
      ]).start();
    }, 1800);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Navigation actions ──────────────────────────────────────────────────────
  const goToResult = () => {
    navigation.navigate('TransactionResult', { transactionData, assessment });
  };

  const handleCancel = () => {
    navigation.goBack();
  };

  const handleGoHome = () => {
    navigation.popToTop();
    navigation.getParent()?.navigate('HomeTab');
  };

  const handleReportBlock = () => {
    Alert.alert(
      'Thanks for letting us know',
      'Our security team will review this within 24 hours. We may contact you to verify a few details.',
      [{ text: 'OK', onPress: handleGoHome }]
    );
  };

  const handleVerify = () => {
    if (mpin.length !== 4) return;
    goToResult();
  };

  // ── Render: checking phase ───────────────────────────────────────────────────
  if (phase === 'checking' || !assessment) {
    return (
      <View style={styles.container}>
        <CheckingView />
      </View>
    );
  }

  // ── Render: result phase ─────────────────────────────────────────────────────
  const decisionStyle = DECISION_STYLES[assessment.decision];
  const zeroDayStyle = ZERO_DAY_STYLES[assessment.zeroDayClass];

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
    >
      <Animated.View
        style={{ opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}
      >
        {/* ── Decision header ── */}
        <View style={styles.decisionHeader}>
          <View
            style={[
              styles.decisionIconWrap,
              { backgroundColor: decisionStyle.bgColor, borderColor: decisionStyle.borderColor },
            ]}
          >
            <Feather name={decisionStyle.icon as any} size={40} color={decisionStyle.color} />
          </View>
          <Text style={[styles.decisionTitle, { color: decisionStyle.color }]}>
            {decisionStyle.title}
          </Text>
          <Text style={styles.decisionSubtitle}>{decisionStyle.subtitle}</Text>
        </View>

        {/* ── Transaction summary ── */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Payment Details</Text>
          <DetailRow label="Amount" value={formatCurrency(transactionData.amount)} />
          <DetailRow
            label="To"
            value={`${transactionData.toLabel} \u00B7 ${transactionData.toDetail}`}
          />
          <DetailRow
            label="From"
            value={`${transactionData.fromAccount.bankName} ${transactionData.fromAccount.masked}`}
          />
          <DetailRow label="Payment Mode" value={transactionData.paymentMode} />
          <DetailRow label="Time" value={formatTime(transactionData.timestamp)} />
        </View>

        {/* ── How unusual is this? (zero-day classification) ── */}
        <View style={[styles.zeroDayCard, { backgroundColor: zeroDayStyle.bgColor }]}>
          <View style={styles.zeroDayHeader}>
            <Feather
              name={
                assessment.zeroDayClass === 'KNOWN'
                  ? 'check-circle'
                  : assessment.zeroDayClass === 'SUSPICIOUS'
                  ? 'alert-triangle'
                  : 'help-circle'
              }
              size={18}
              color={zeroDayStyle.color}
            />
            <Text style={[styles.zeroDayLabel, { color: zeroDayStyle.color }]}>
              {zeroDayStyle.label}
            </Text>
          </View>
          <Text style={styles.zeroDaySublabel}>{zeroDayStyle.sublabel}</Text>
        </View>

        {/* ── What we checked ── */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>What We Checked</Text>
          {assessment.signalIds.length === 0 ? (
            <View style={styles.allClearRow}>
              <Feather name="check-circle" size={16} color={COLORS.success} />
              <Text style={styles.allClearText}>
                Everything matches your usual activity — no concerns found.
              </Text>
            </View>
          ) : (
            assessment.signalIds.map((id) => (
              <SignalRow
                key={id}
                signalId={id}
                expanded={expandedSignal === id}
                onToggle={() => setExpandedSignal((prev) => (prev === id ? null : id))}
              />
            ))
          )}
        </View>

        {/* ── BLOCK: audit reassurance ── */}
        {assessment.decision === 'BLOCK' && (
          <View style={styles.auditNote}>
            <Feather name="lock" size={14} color={COLORS.textTertiary} />
            <Text style={styles.auditNoteText}>
              This has been securely recorded for your protection. No money has left your
              account.
            </Text>
          </View>
        )}

        {/* ── CHALLENGE: quick verification ── */}
        {assessment.decision === 'CHALLENGE' && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Quick Verification</Text>
            <Text style={styles.verifyHint}>
              For your safety, please re-enter your 4-digit MPIN to confirm this payment.
            </Text>
            <TextInput
              style={styles.mpinInput}
              value={mpin}
              onChangeText={(t) => setMpin(t.replace(/[^\d]/g, '').slice(0, 4))}
              keyboardType="number-pad"
              secureTextEntry
              maxLength={4}
              placeholder="• • • •"
              placeholderTextColor={COLORS.textTertiary}
              textAlign="center"
            />
          </View>
        )}

        {/* ── Action buttons ── */}
        <View style={styles.actions}>
          {assessment.decision === 'ALLOW' && (
            <TouchableOpacity style={styles.primaryBtn} onPress={goToResult} activeOpacity={0.8}>
              <Text style={styles.primaryBtnText}>Continue</Text>
              <Feather name="arrow-right" size={18} color={COLORS.textOnDark} />
            </TouchableOpacity>
          )}

          {assessment.decision === 'WARN' && (
            <>
              <TouchableOpacity
                style={styles.primaryBtn}
                onPress={goToResult}
                activeOpacity={0.8}
              >
                <Text style={styles.primaryBtnText}>Continue Payment</Text>
                <Feather name="arrow-right" size={18} color={COLORS.textOnDark} />
              </TouchableOpacity>
              <TouchableOpacity style={styles.textLinkBtn} onPress={handleCancel} activeOpacity={0.7}>
                <Text style={styles.textLinkText}>Cancel and go back</Text>
              </TouchableOpacity>
            </>
          )}

          {assessment.decision === 'CHALLENGE' && (
            <>
              <TouchableOpacity
                style={[styles.primaryBtn, mpin.length !== 4 && styles.primaryBtnDisabled]}
                onPress={handleVerify}
                disabled={mpin.length !== 4}
                activeOpacity={0.8}
              >
                <Feather name="shield" size={16} color={COLORS.textOnDark} />
                <Text style={styles.primaryBtnText}>Verify & Continue</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.textLinkBtn} onPress={handleCancel} activeOpacity={0.7}>
                <Text style={styles.textLinkText}>Cancel and go back</Text>
              </TouchableOpacity>
            </>
          )}

          {assessment.decision === 'BLOCK' && (
            <>
              <TouchableOpacity style={styles.primaryBtn} onPress={handleGoHome} activeOpacity={0.8}>
                <Feather name="home" size={16} color={COLORS.textOnDark} />
                <Text style={styles.primaryBtnText}>Go to Home</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.secondaryBtn}
                onPress={handleReportBlock}
                activeOpacity={0.8}
              >
                <Feather name="flag" size={16} color={COLORS.primary} />
                <Text style={styles.secondaryBtnText}>This Was Me — Report Issue</Text>
              </TouchableOpacity>
            </>
          )}
        </View>

        <View style={{ height: insets.bottom + SPACING.xl }} />
      </Animated.View>
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

  // Checking phase
  checkingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: SPACING.xl,
  },
  checkingIconWrap: {
    width: 96,
    height: 96,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.primaryVeryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.xl,
  },
  checkingTitle: {
    ...TYPOGRAPHY.h3,
    color: COLORS.text,
    fontWeight: '700',
    marginBottom: SPACING.sm,
  },
  checkingStep: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginBottom: SPACING.xl,
  },
  checkingHint: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
  },

  // Decision header
  decisionHeader: {
    alignItems: 'center',
    marginBottom: SPACING.lg,
    paddingTop: SPACING.md,
  },
  decisionIconWrap: {
    width: 88,
    height: 88,
    borderRadius: BORDER_RADIUS.full,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1.5,
    marginBottom: SPACING.md,
  },
  decisionTitle: {
    ...TYPOGRAPHY.h2,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: SPACING.xs,
  },
  decisionSubtitle: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    textAlign: 'center',
    paddingHorizontal: SPACING.lg,
  },

  // Card
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    marginBottom: SPACING.md,
    ...SHADOWS.small,
  },
  cardTitle: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.text,
    fontWeight: '700',
    marginBottom: SPACING.sm,
  },

  // Detail row
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: SPACING.xs,
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

  // Zero-day card
  zeroDayCard: {
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    marginBottom: SPACING.md,
  },
  zeroDayHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginBottom: 4,
  },
  zeroDayLabel: {
    ...TYPOGRAPHY.bodySmMedium,
    fontWeight: '700',
  },
  zeroDaySublabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
  },

  // All clear row
  allClearRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    paddingVertical: SPACING.xs,
  },
  allClearText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    flex: 1,
  },

  // Signal row
  signalRow: {
    borderTopWidth: 1,
    borderTopColor: COLORS.divider,
    paddingVertical: SPACING.sm,
  },
  signalRowHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
  },
  signalIconWrap: {
    width: 32,
    height: 32,
    borderRadius: BORDER_RADIUS.md,
    justifyContent: 'center',
    alignItems: 'center',
  },
  signalName: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.text,
    fontWeight: '600',
    flex: 1,
  },
  signalExplanation: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginTop: SPACING.sm,
    marginLeft: 40,
    lineHeight: 19,
  },

  // Audit note
  auditNote: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: SPACING.sm,
    backgroundColor: COLORS.surfaceLight,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.md,
  },
  auditNoteText: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    flex: 1,
    lineHeight: 17,
  },

  // Verification (CHALLENGE)
  verifyHint: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginBottom: SPACING.md,
  },
  mpinInput: {
    backgroundColor: COLORS.surfaceLight,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.lg,
    paddingVertical: SPACING.md,
    fontSize: 24,
    letterSpacing: 12,
    color: COLORS.text,
    fontWeight: '700',
  },

  // Actions
  actions: {
    gap: SPACING.sm,
    marginTop: SPACING.sm,
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
  primaryBtnDisabled: {
    backgroundColor: COLORS.borderDark,
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
  textLinkBtn: {
    alignItems: 'center',
    paddingVertical: SPACING.sm,
  },
  textLinkText: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.textSecondary,
  },
});

export default SecurityReviewScreen;