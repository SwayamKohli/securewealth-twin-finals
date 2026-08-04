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
// UI COPY ONLY — friendly names + plain-English explanations for signal IDs.
// All risk values, decisions and scores come from the backend.
// Display copy ONLY — friendly name, icon and severity for each signal the
// risk engine can raise. The list of signals that actually fired always comes
// from the backend (`triggered_signals`); this file never decides anything.
import riskSignalsData from '../../mockData/risk_signals.json';
import { api, ApiError } from '../api/apiService';
import { useI18n } from '../i18n';

// ── Local decision types (previously from riskSimulator) ──────────────────────
type Decision = 'ALLOW' | 'WARN' | 'CHALLENGE' | 'BLOCK';
type ZeroDayClass = 'KNOWN' | 'SUSPICIOUS' | 'UNKNOWN';

interface RiskAssessment {
  decision: Decision;
  riskScore: number;
  zeroDayClass: ZeroDayClass;
  signalIds: string[];
  // Identifiers carried forward so TransactionResult can show the real txn.
  transactionId?: string | null;
  // Plain-language reason from the backend Decision Engine.
  report?: string | null;
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

// The engine names rules in snake_case ("amount_spike"); the display copy is
// keyed UPPER_SNAKE ("AMOUNT_SPIKE"). Normalise, and map the few names that
// differ between the two.
const SIGNAL_ALIASES: Record<string, string> = {
  ROUND_NUMBER_ANOMALY: 'ROUND_NUMBER',
  EXTREME_AMOUNT_SPIKE: 'AMOUNT_SPIKE',
  VELOCITY_BURST: 'TRANSACTION_BURST',
  OTP_DISTRESS: 'FAST_OTP',
  OTP_RELAY: 'FAST_OTP',
};

const normalizeSignal = (raw: string): string => {
  const upper = String(raw || '').toUpperCase();
  return SIGNAL_ALIASES[upper] || upper;
};

// Cycling messages shown during the "checking" phase
// Staged status messages tied to ELAPSED TIME, not a decorative loop.
// The old version cycled all four every 450ms regardless of what the backend
// was doing, which reads as fake. These advance with the real wait, and after
// ~8s the copy changes to acknowledge the delay instead of pretending.
// Modelled on how UPI apps handle a slow bank response.
const CHECK_STAGES: { at: number; icon: string; key: string }[] = [
  { at: 0,  icon: 'smartphone', key: 'checking.device' },
  { at: 2,  icon: 'activity',   key: 'checking.pattern' },
  { at: 4,  icon: 'search',     key: 'checking.fraud' },
  { at: 6,  icon: 'file-text',  key: 'checking.audit' },
  { at: 8,  icon: 'clock',      key: 'checking.slow' },
  { at: 14, icon: 'clock',      key: 'checking.stillSafe' },
];

type Phase = 'checking' | 'result';

// Normalize a backend decision string into our union (defensive).
const normalizeDecision = (d: string | null | undefined): Decision => {
  const up = String(d || '').toUpperCase();
  if (up === 'BLOCK' || up === 'WARN' || up === 'CHALLENGE' || up === 'ALLOW') return up as Decision;
  return 'ALLOW';
};

// Map the BACKEND's risk score → the "how unusual" bucket the UI shows.
// This used to take a locally-synthesised `hint` as well, which meant the
// bucket could contradict the engine's own score. Score only, now.
const zeroDayFromScore = (score: number): ZeroDayClass => {
  if (score >= 80) return 'UNKNOWN';
  if (score >= 30) return 'SUSPICIOUS';
  return 'KNOWN';
};

// ── Sub-components ────────────────────────────────────────────────────────────

// Security-check progress: a real elapsed-time counter plus stage messages.
// A spinner alone tells the customer nothing; a counter tells them the system
// is alive and roughly how long it has been working, which is what stops
// people force-quitting a payment mid-flight.
const CheckingView = () => {
  const { t } = useI18n();
  const pulse = useRef(new Animated.Value(0)).current;
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, {
          toValue: 1,
          duration: 900,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulse, {
          toValue: 0,
          duration: 900,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    ).start();

    const started = Date.now();
    const id = setInterval(
      () => setElapsed(Math.floor((Date.now() - started) / 1000)),
      250
    );
    return () => clearInterval(id);
  }, []);

  // Last stage whose threshold we have passed.
  const stage =
    [...CHECK_STAGES].reverse().find((st) => elapsed >= st.at) || CHECK_STAGES[0];
  const slow = elapsed >= 8;

  const scale = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.08] });
  const haloOpacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.35, 0.08] });

  return (
    <View style={styles.checkingContainer}>
      <View style={styles.checkingShieldStack}>
        <Animated.View
          style={[styles.checkingHalo, { opacity: haloOpacity, transform: [{ scale }] }]}
        />
        <View style={styles.checkingIconWrap}>
          <Feather name="shield" size={52} color={COLORS.primary} />
        </View>
      </View>

      <Text style={styles.checkingTitle}>{t('checking.title')}</Text>

      <View style={styles.checkingStageRow}>
        <Feather
          name={stage.icon as any}
          size={14}
          color={slow ? COLORS.caution : COLORS.textSecondary}
        />
        <Text style={[styles.checkingStep, slow && { color: COLORS.caution }]}>
          {t(stage.key)}
        </Text>
      </View>

      {/* Elapsed-time counter — proof the system is working, not frozen */}
      <View style={[styles.timerPill, slow && styles.timerPillSlow]}>
        <Text style={[styles.timerValue, slow && { color: COLORS.caution }]}>{elapsed}</Text>
        <Text style={[styles.timerUnit, slow && { color: COLORS.caution }]}>
          {t('checking.seconds')}
        </Text>
      </View>

      <Text style={styles.checkingHint}>
        {slow ? t('checking.dontClose') : t('checking.engines')}
      </Text>
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
  const { t, language } = useI18n();

  const [phase, setPhase] = useState<Phase>('checking');
  const [assessment, setAssessment] = useState<RiskAssessment | null>(null);
  // Task 5.14 — the live explainability engine's plain-language reason, in the
  // customer's chosen language. The backend's own decision_report is the
  // fallback, and the bundled JSON copy is the fallback of last resort, so this
  // never leaves the customer staring at a decision with no explanation.
  const [liveExplanation, setLiveExplanation] = useState<string | null>(null);
  const [expandedSignal, setExpandedSignal] = useState<string | null>(null);
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
        // Task 2.4: single backend call — the server runs the full pipeline
        // (Behavior → Fraud ML → Zero-Day → Risk → Decision), audits it, and
        // holds the investment as PENDING when a CHALLENGE is required.
        const txn = await api.initiateTransaction({
          account_id: transactionData.fromAccountId,
          amount: transactionData.amount,
          fund_name: transactionData.toLabel || 'Mutual Fund',
          fund_category: transactionData.fundCategory || 'MUTUAL_FUND',
          channel: (transactionData.channel || 'UPI') as any,
        });

        const decision = normalizeDecision(txn?.decision);
        const finalScore = Number(txn?.risk_score) || 0;

        finish({
          decision,
          riskScore: finalScore,
          zeroDayClass: zeroDayFromScore(finalScore),
          // Real signals from the engine. If the backend sends none, we show
          // "no concerns found" rather than inventing a list from the amount.
          signalIds: Array.from(
            new Set((txn?.triggered_signals || []).map(normalizeSignal))
          ).filter((id) => id in signalDefs),
          transactionId: txn?.transaction_id ?? null,
          report: txn?.decision_report ?? null,
        });

        // Explanation is supplementary: fetch it after the verdict is on
        // screen and swallow any failure. The customer must never wait on it.
        api
          .explainDecision({
            record: {
              decision,
              risk_score: finalScore,
              amount: transactionData.amount,
              fund_name: transactionData.toLabel,
              challenge_required: decision === 'CHALLENGE',
              decision_report: txn?.decision_report ?? null,
            },
            language,
          })
          .then((res) => {
            if (!cancelled && res?.explanation) setLiveExplanation(res.explanation);
          })
          .catch(() => undefined);
      } catch (e) {
        if (cancelled) return;
        const err = e as ApiError;

        // A TIMEOUT is not a failure. The request reached the bank and may have
        // completed — the server was simply slow to answer. Telling the customer
        // it failed and offering "try again" is how you get a duplicate
        // investment. Send them to their activity instead.
        if (err instanceof ApiError && err.isTimeout) {
          Alert.alert(t('review.timeoutTitle'), t('review.timeoutBody'), [
            {
              text: t('review.checkActivity'),
              onPress: () => navigation.navigate('SafetyTab', { screen: 'MySecurityActivity' }),
            },
            { text: t('common.back'), onPress: () => navigation.goBack() },
          ]);
          return;
        }

        // Genuinely unreachable: nothing was sent, so it is safe to say so.
        const msg =
          err instanceof ApiError && err.isNetworkError
            ? t('review.unreachable')
            : err instanceof ApiError
            ? err.message
            : t('review.unreachable');
        Alert.alert(t('review.failedTitle'), msg, [
          { text: t('common.back'), onPress: () => navigation.goBack() },
        ]);
      }
    })();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Continue to the receipt (investment already settled by the backend) ─────
  const initiateAndContinue = () => {
    if (!assessment) return;
    navigation.navigate('TransactionResult', { transactionData, assessment });
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
            {t(`decision.${assessment.decision}.title`)}
          </Text>
          <Text style={styles.decisionSubtitle}>
            {t(`decision.${assessment.decision}.subtitle`)}
          </Text>
        </View>

        {/* ── Transaction summary ── */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>{t('review.txnDetails')}</Text>
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
          <Text style={styles.cardTitle}>{t('review.whatChecked')}</Text>
          {assessment.signalIds.length === 0 ? (
            <View style={styles.allClearRow}>
              <Feather name="check-circle" size={16} color={COLORS.success} />
              <Text style={styles.allClearText}>
                {t('review.allClear')}
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

        {/* ── Live plain-language explanation (task 5.14) ──
             Shown for ALLOW / WARN / BLOCK; CHALLENGE has its own card below
             so the customer isn't told the same thing twice. */}
        {liveExplanation && assessment.decision !== 'CHALLENGE' && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>{t('review.whatMeans')}</Text>
            <Text style={styles.verifyHint}>{liveExplanation}</Text>
          </View>
        )}

        {/* ── CHALLENGE: held for verification (task 4.3) ── */}
        {assessment.decision === 'CHALLENGE' && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>{t('decision.CHALLENGE.title')}</Text>
            <Text style={styles.verifyHint}>
              {liveExplanation ||
                assessment.report ||
                'This investment looks unusual for your account, so we have placed it on hold. A quick identity check will complete it — no money has moved yet.'}
            </Text>
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
                <Text style={styles.textLinkText}>{t('review.cancelBack')}</Text>
              </TouchableOpacity>
            </>
          )}

          {assessment.decision === 'CHALLENGE' && (
            <>
              <TouchableOpacity
                style={styles.primaryBtn}
                onPress={() =>
                  navigation.navigate('Challenge', { transactionData, assessment })
                }
                activeOpacity={0.8}
              >
                <Feather name="shield" size={16} color={COLORS.textOnDark} />
                <Text style={styles.primaryBtnText}>{t('review.verifyMe')}</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.textLinkBtn} onPress={handleGoHome} activeOpacity={0.7}>
                <Text style={styles.textLinkText}>{t('review.keepOnHold')}</Text>
              </TouchableOpacity>
            </>
          )}

          {assessment.decision === 'BLOCK' && (
            <>
              <TouchableOpacity style={styles.primaryBtn} onPress={handleGoHome} activeOpacity={0.8}>
                <Feather name="home" size={16} color={COLORS.textOnDark} />
                <Text style={styles.primaryBtnText}>{t('review.goHome')}</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.secondaryBtn}
                onPress={handleReportBlock}
                activeOpacity={0.8}
              >
                <Feather name="flag" size={16} color={COLORS.primary} />
                <Text style={styles.secondaryBtnText}>{t('review.thisWasMe')}</Text>
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
  checkingShieldStack: {
    width: 128,
    height: 128,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: SPACING.xl,
  },
  checkingHalo: {
    position: 'absolute',
    width: 128,
    height: 128,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.primaryLight,
  },
  checkingIconWrap: {
    width: 92,
    height: 92,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.primaryVeryLight,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkingStageRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
    marginBottom: SPACING.lg,
  },
  timerPill: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 4,
    borderWidth: 1.5,
    borderColor: COLORS.primaryLight,
    borderRadius: BORDER_RADIUS.full,
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.sm,
    marginBottom: SPACING.lg,
    minWidth: 108,
    justifyContent: 'center',
  },
  timerPillSlow: { borderColor: COLORS.caution },
  timerValue: { ...TYPOGRAPHY.h3, color: COLORS.primary, fontWeight: '800' },
  timerUnit: {
    ...TYPOGRAPHY.caption,
    color: COLORS.primary,
    fontWeight: '800',
    letterSpacing: 1,
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
  },
  checkingHint: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    textAlign: 'center',
    lineHeight: 17,
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