// src/screens/SecurityReviewScreen.tsx
// SecureWealth Twin — Security Check
//
// BACKEND INTEGRATION (was local assessTransaction() simulator):
//  • The "checking" phase now runs the REAL decision chain:
//      POST /ai/fraud/evaluate → POST /security/risk/evaluate → POST /security/decision/make
//    Risk signals the UI can't collect are synthesized (utils/riskBuilder.ts),
//    preserving the old demo thresholds. The BACKEND's decision drives the UI.
//  • Money moves on Continue / Verify (not before): POST /transactions/initiate.
//    BLOCK never initiates and stays non-resumable (unchanged guarantee).
//  • Falls back to the local synthesized decision only if the API is unreachable,
//    so the demo still works offline.
//  • UI phases, animations, DECISION_STYLES, and styles are unchanged.

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
import riskSignalsData from '../../mockData/risk_signals.json';
import { api, ApiError } from '../api/apiService';
import {
  synthesizeProfile,
  buildFraudRequest,
  buildRiskRequest,
  buildDecisionRequest,
  signalIdsFor,
  type SynthInput,
} from '../utils/riskBuilder';

// ── Local decision types (previously from riskSimulator) ──────────────────────
type Decision = 'ALLOW' | 'WARN' | 'CHALLENGE' | 'BLOCK';
type ZeroDayClass = 'KNOWN' | 'SUSPICIOUS' | 'UNKNOWN';

interface RiskAssessment {
  decision: Decision;
  riskScore: number;
  zeroDayClass: ZeroDayClass;
  signalIds: string[];
  // NEW: identifiers carried forward so TransactionResult can show the real txn.
  transactionId?: string | null;
}

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

// Normalize a backend decision string into our union (defensive).
const normalizeDecision = (d: string | null | undefined): Decision => {
  const up = String(d || '').toUpperCase();
  if (up === 'BLOCK' || up === 'WARN' || up === 'CHALLENGE' || up === 'ALLOW') return up as Decision;
  return 'ALLOW';
};

// Map a numeric risk score → the zero-day "how unusual" bucket the UI shows.
const zeroDayFromScore = (score: number, hint: string): ZeroDayClass => {
  if (hint === 'FRAUD' || score >= 80) return 'UNKNOWN';
  if (score >= 30) return 'SUSPICIOUS';
  return 'KNOWN';
};

// Pure-local fallback decision (mirrors the old simulator thresholds) so the
// demo still resolves if the network is down.
const localFallback = (input: SynthInput): RiskAssessment => {
  const p = synthesizeProfile(input);
  const map: Record<string, { decision: Decision; score: number }> = {
    FRAUD: { decision: 'BLOCK', score: 92 },
    SPIKE: { decision: 'WARN', score: 38 },
    NEW_RECIPIENT: { decision: 'CHALLENGE', score: 55 },
    CLEAN: { decision: 'ALLOW', score: 8 },
  };
  const r = map[p.hint];
  return {
    decision: r.decision,
    riskScore: r.score,
    zeroDayClass: zeroDayFromScore(r.score, p.hint),
    signalIds: signalIdsFor(p.hint),
  };
};

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
  const [processing, setProcessing] = useState(false); // initiate in flight

  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(16)).current;

  const revealResult = () => {
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
  };

  useEffect(() => {
    let cancelled = false;
    const startedAt = Date.now();
    const MIN_CHECK_MS = 1800; // keep the reassuring animation duration

    const input: SynthInput = {
      amount: transactionData.amount,
      isNewRecipient: transactionData.isNewRecipient,
    };
    const profile = synthesizeProfile(input);

    const finish = (result: RiskAssessment) => {
      const elapsed = Date.now() - startedAt;
      const wait = Math.max(0, MIN_CHECK_MS - elapsed);
      setTimeout(() => {
        if (cancelled) return;
        setAssessment(result);
        revealResult();
      }, wait);
    };

    (async () => {
      try {
        // 1) Fraud probability
        const fraud = await api.evaluateFraud(buildFraudRequest(input));
        const fraudProb = Number(fraud?.fraud_probability) || 0;
        const confidence = Number(fraud?.confidence) || 0;

        // 2) Risk score (combines synthesized signals + AI fraud output)
        const risk = await api.evaluateRisk(buildRiskRequest(input, fraudProb, confidence));
        const riskScore = Number(risk?.risk_score) || 0;

        // 3) Final decision. We don't have a real transaction_id yet (money moves
        //    on Continue), so we pass a placeholder for the decision preview.
        const decisionRes = await api.makeDecision(
          buildDecisionRequest(input, {
            transactionId: 'preview',
            accountId: transactionData.fromAccountId || 'self',
            channel: transactionData.channel || transactionData.paymentMode || 'IMPS',
            aiFraudProbability: fraudProb,
            aiConfidence: confidence,
          })
        );

        const decision = normalizeDecision(decisionRes?.decision);
        const finalScore = Number(decisionRes?.risk_score ?? riskScore) || riskScore;

        finish({
          decision,
          riskScore: finalScore,
          zeroDayClass: zeroDayFromScore(finalScore, profile.hint),
          signalIds: signalIdsFor(profile.hint),
        });
      } catch (e) {
        // Network/API failure → deterministic local fallback so the demo continues.
        finish(localFallback(input));
      }
    })();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Initiate the real transaction, then go to the receipt ────────────────────
  const initiateAndContinue = async () => {
    if (!assessment) return;

    // If we don't have the identifiers needed to initiate, just show the receipt
    // (keeps the flow working even if TransactionInitiate wasn't updated).
    if (!transactionData.fromAccountId) {
      navigation.navigate('TransactionResult', { transactionData, assessment });
      return;
    }

    setProcessing(true);
    try {
      const txn = await api.initiateTransaction({
        account_id: transactionData.fromAccountId,
        amount: transactionData.amount,
        merchant_name: transactionData.toLabel || 'Recipient',
        merchant_category: 'Transfer',
        channel: (transactionData.channel || 'IMPS') as any,
      });

      // Prefer the backend's decision on the actual transaction if present.
      const backendDecision = normalizeDecision(txn?.decision ?? assessment.decision);
      const finalAssessment: RiskAssessment = {
        ...assessment,
        decision: backendDecision,
        transactionId: txn?.transaction_id ?? null,
      };
      navigation.navigate('TransactionResult', {
        transactionData,
        assessment: finalAssessment,
      });
    } catch (e) {
      const err = e as ApiError;
      const msg =
        err instanceof ApiError && err.isNetworkError
          ? 'We could not reach the server to complete your payment. Please try again.'
          : err instanceof ApiError
          ? err.message
          : 'Something went wrong completing your payment.';
      Alert.alert('Payment could not be completed', msg, [{ text: 'OK' }]);
    } finally {
      setProcessing(false);
    }
  };

  // ── Navigation actions ──────────────────────────────────────────────────────
  const goToResult = () => {
    initiateAndContinue();
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
              placeholder="\u2022 \u2022 \u2022 \u2022"
              placeholderTextColor={COLORS.textTertiary}
              textAlign="center"
            />
          </View>
        )}

        {/* ── Action buttons ── */}
        <View style={styles.actions}>
          {assessment.decision === 'ALLOW' && (
            <TouchableOpacity
              style={[styles.primaryBtn, processing && styles.primaryBtnDisabled]}
              onPress={goToResult}
              disabled={processing}
              activeOpacity={0.8}
            >
              <Text style={styles.primaryBtnText}>{processing ? 'Processing\u2026' : 'Continue'}</Text>
              {!processing && <Feather name="arrow-right" size={18} color={COLORS.textOnDark} />}
            </TouchableOpacity>
          )}

          {assessment.decision === 'WARN' && (
            <>
              <TouchableOpacity
                style={[styles.primaryBtn, processing && styles.primaryBtnDisabled]}
                onPress={goToResult}
                disabled={processing}
                activeOpacity={0.8}
              >
                <Text style={styles.primaryBtnText}>
                  {processing ? 'Processing\u2026' : 'Continue Payment'}
                </Text>
                {!processing && <Feather name="arrow-right" size={18} color={COLORS.textOnDark} />}
              </TouchableOpacity>
              <TouchableOpacity style={styles.textLinkBtn} onPress={handleCancel} activeOpacity={0.7}>
                <Text style={styles.textLinkText}>Cancel and go back</Text>
              </TouchableOpacity>
            </>
          )}

          {assessment.decision === 'CHALLENGE' && (
            <>
              <TouchableOpacity
                style={[styles.primaryBtn, (mpin.length !== 4 || processing) && styles.primaryBtnDisabled]}
                onPress={handleVerify}
                disabled={mpin.length !== 4 || processing}
                activeOpacity={0.8}
              >
                <Feather name="shield" size={16} color={COLORS.textOnDark} />
                <Text style={styles.primaryBtnText}>
                  {processing ? 'Processing\u2026' : 'Verify & Continue'}
                </Text>
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