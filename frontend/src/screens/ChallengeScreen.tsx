// src/screens/ChallengeScreen.tsx
// SecureWealth Twin — Challenge Verification (task 4.3)
//
// Adaptive step-up verification for investments the Decision Engine put on
// hold. The backend decides WHICH steps are needed (security question, MPIN,
// risk acknowledgement, OTP) — OTP appears only when required. On success the
// backend completes the held investment and we show the receipt.
//
// M3 additions:
//   • Method picker (4.3b) — "Can't access your OTP? Verify another way."
//     Verification stays mandatory; the customer chooses HOW. The backend
//     refuses any swap that lowers assurance, and adds a compensating step
//     when a weaker factor class is chosen.
//   • "This wasn't me" (4.3c) — drops the held investment and records it in
//     the audit chain as a customer-reported fraud attempt.
//   • OTP countdown + resend, attempts-left meter, and a persistent
//     "your money hasn't moved" banner.

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  ActivityIndicator,
  Alert,
  Modal,
  Animated,
} from 'react-native';
import { Feather } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import { api, ApiError } from '../api/apiService';
import type { ChallengeStepResponse, ChallengeMethodOption } from '../api/types';
import { useI18n } from '../i18n';

const STEP_META: Record<string, { icon: string; title: string }> = {
  SECURITY_QUESTION: { icon: 'help-circle', title: 'Security Question' },
  MPIN: { icon: 'key', title: 'Confirm MPIN' },
  OTP: { icon: 'smartphone', title: 'One-Time Password' },
  ACKNOWLEDGE: { icon: 'alert-triangle', title: 'Review & Confirm' },
};

const METHOD_ICONS: Record<string, string> = {
  OTP: 'smartphone',
  MPIN: 'key',
  SECURITY_QUESTION: 'help-circle',
  BIOMETRIC: 'user-check',
};

const OTP_TTL_SECONDS = 5 * 60; // matches OTP_TTL_MINUTES on the backend

const formatCurrency = (n: number) => '₹' + n.toLocaleString('en-IN');
const mmss = (secs: number) =>
  `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')}`;

const ChallengeScreen = ({ route, navigation }: any) => {
  const { t, language } = useI18n();
  const { transactionData, assessment } = route.params;
  const transactionId: string | null = assessment?.transactionId ?? null;

  const [step, setStep] = useState<ChallengeStepResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [answer, setAnswer] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [demoOtp, setDemoOtp] = useState<string | null>(null);

  // Method picker
  const [methodsOpen, setMethodsOpen] = useState(false);
  const [methods, setMethods] = useState<ChallengeMethodOption[]>([]);
  const [methodsNote, setMethodsNote] = useState('');
  const [methodsLoading, setMethodsLoading] = useState(false);
  const [switching, setSwitching] = useState(false);

  // OTP expiry countdown
  const [secondsLeft, setSecondsLeft] = useState(0);

  // Task 4.3 — WHY this verification is being asked for, from the Challenge
  // Explainability engine. Another backend engine that nothing was calling.
  // Fetched once per challenge, in the customer's language.
  const [whyChallenged, setWhyChallenged] = useState<string | null>(null);

  const shake = useRef(new Animated.Value(0)).current;

  const runShake = () => {
    shake.setValue(0);
    Animated.sequence([
      Animated.timing(shake, { toValue: 1, duration: 60, useNativeDriver: true }),
      Animated.timing(shake, { toValue: -1, duration: 60, useNativeDriver: true }),
      Animated.timing(shake, { toValue: 0.6, duration: 60, useNativeDriver: true }),
      Animated.timing(shake, { toValue: 0, duration: 60, useNativeDriver: true }),
    ]).start();
  };

  /** Apply a step payload consistently, wherever it came from. */
  const applyStep = useCallback((s: ChallengeStepResponse) => {
    setStep(s);
    setAnswer('');
    if (s.demo_otp) setDemoOtp(s.demo_otp);
    if (s.current_step === 'OTP') {
      if (s.demo_otp) setSecondsLeft(OTP_TTL_SECONDS);
    } else {
      setSecondsLeft(0);
      setDemoOtp(null);
    }
  }, []);

  const finish = (status: 'SUCCESS' | 'FAILED', message?: string) => {
    navigation.navigate('TransactionResult', {
      transactionData,
      assessment: {
        ...assessment,
        decision: status === 'SUCCESS' ? 'CHALLENGE' : 'BLOCK',
        verified: status === 'SUCCESS',
        report:
          message ||
          (status === 'SUCCESS'
            ? 'Identity verified. Your investment has been completed.'
            : 'Verification failed. The investment was cancelled.'),
      },
    });
  };

  /**
   * The challenge may already be over without this screen knowing — either the
   * verify reply was lost to a timeout while the server completed it, or the
   * server says the transaction is no longer awaiting verification.
   *
   * Both cases have the same correct response: stop guessing and ask what the
   * transaction's real status is, then show that. Never leave the customer on a
   * verification screen for an investment that has already settled.
   *
   * Returns true when it resolved and navigated away.
   */
  const resolveIfSettled = useCallback(async (): Promise<boolean> => {
    if (!transactionId) return false;
    try {
      const txn = await api.getTransactionStatus(transactionId);
      const st = String(txn?.status || '').toUpperCase();
      if (st === 'SUCCESS') {
        finish('SUCCESS');
        return true;
      }
      if (st === 'FAILED' || st === 'BLOCKED') {
        finish('FAILED');
        return true;
      }
      return false; // still PENDING — the challenge really is live
    } catch {
      return false;
    }
  }, [transactionId]);

  const load = useCallback(async () => {
    if (!transactionId) {
      Alert.alert('Verification unavailable', 'Missing transaction reference.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
      return;
    }
    setLoading(true);
    try {
      applyStep(await api.startChallenge(transactionId));
    } catch (e) {
      const err = e as ApiError;
      // If the investment already settled, show the result rather than an error.
      if (await resolveIfSettled()) {
        setLoading(false);
        return;
      }
      Alert.alert(
        t('challenge.alreadyDone'),
        err instanceof ApiError ? err.message : t('common.tryAgain'),
        [{ text: t('common.back'), onPress: () => navigation.goBack() }]
      );
    } finally {
      setLoading(false);
    }
  }, [transactionId, applyStep, resolveIfSettled]);

  useEffect(() => {
    load();
  }, [load]);

  // Explanation is supplementary — never gate the verification on it.
  useEffect(() => {
    if (!transactionId || !step?.challenge_type || whyChallenged) return;
    api
      .explainChallenge({
        requirement: {
          challenge_type: step.challenge_type,
          trigger_signal: step.trigger_signal,
        },
        language,
      })
      .then((res) => setWhyChallenged(res?.explanation || null))
      .catch(() => undefined);
  }, [transactionId, step?.challenge_type, step?.trigger_signal, language, whyChallenged]);

  // Countdown tick — only runs while a code is actually live.
  const ticking = secondsLeft > 0;
  useEffect(() => {
    if (!ticking) return;
    const id = setInterval(() => setSecondsLeft((s) => (s > 0 ? s - 1 : 0)), 1000);
    return () => clearInterval(id);
  }, [ticking]);

  const submit = async (acknowledged = false) => {
    if (!transactionId || !step) return;
    setSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      const r = await api.verifyChallenge(transactionId, {
        answer: answer || undefined,
        acknowledged,
      });
      if (r.completed && r.transaction_status) {
        finish(r.transaction_status, r.message);
        return;
      }
      applyStep(r);
      if (r.verified === false) {
        setError(r.message || 'That did not match. Try again.');
        runShake();
      } else if (r.message) {
        setNotice(r.message);
      }
    } catch (e) {
      const err = e as ApiError;

      // Timeout: the server probably finished. Ask before saying anything.
      if (err instanceof ApiError && err.isTimeout) {
        setNotice(t('challenge.slowConfirm'));
        const settled = await resolveIfSettled();
        if (!settled) setError(t('challenge.stillPending'));
        setSubmitting(false);
        return;
      }

      // 400 "not awaiting verification": the challenge is already over. This is
      // not an error to show the customer — it is a stale screen.
      if (err instanceof ApiError && err.status === 400) {
        const settled = await resolveIfSettled();
        if (settled) {
          setSubmitting(false);
          return;
        }
      }

      setError(err instanceof ApiError ? err.message : t('common.tryAgain'));
      runShake();
    } finally {
      setSubmitting(false);
    }
  };

  // ── Method picker ──────────────────────────────────────────────────────
  const openMethods = async () => {
    if (!transactionId) return;
    setMethodsOpen(true);
    setMethodsLoading(true);
    try {
      const res = await api.getChallengeMethods(transactionId);
      setMethods(res.methods);
      setMethodsNote(res.note);
    } catch {
      setMethods([]);
      setMethodsNote('We could not load the alternatives right now.');
    } finally {
      setMethodsLoading(false);
    }
  };

  const chooseMethod = async (option: ChallengeMethodOption) => {
    if (!transactionId || option.is_current || !option.available) return;
    setSwitching(true);
    try {
      const r = await api.switchChallengeMethod(transactionId, option.method);
      applyStep(r);
      setMethodsOpen(false);
      setError(null);
      setNotice(r.message || 'Verification method changed.');
    } catch (e) {
      const err = e as ApiError;
      Alert.alert(
        'Could not switch method',
        err instanceof ApiError ? err.message : 'Please try again.'
      );
    } finally {
      setSwitching(false);
    }
  };

  const resendOtp = async () => {
    if (!transactionId) return;
    try {
      const r = await api.resendChallengeOtp(transactionId);
      applyStep(r);
      setSecondsLeft(OTP_TTL_SECONDS);
      setNotice(r.message || 'A new one-time password has been sent.');
      setError(null);
    } catch (e) {
      const err = e as ApiError;
      setError(err instanceof ApiError ? err.message : 'Could not resend the OTP.');
    }
  };

  // ── "This wasn't me" ───────────────────────────────────────────────────
  const notMe = () => {
    Alert.alert(
      'You did not start this?',
      'We will stop this investment immediately. No money has left your account, '
        + 'and we will record this as a suspected fraud attempt.',
      [
        { text: 'Go back', style: 'cancel' },
        {
          text: "Yes, this wasn't me",
          style: 'destructive',
          onPress: async () => {
            if (!transactionId) return;
            setSubmitting(true);
            try {
              const r = await api.cancelChallenge(transactionId, 'not_me');
              Alert.alert('Investment stopped', r.message, [
                { text: 'OK', onPress: () => finish('FAILED', r.message) },
              ]);
            } catch (e) {
              const err = e as ApiError;
              // Already settled — nothing to cancel. Show the outcome instead
              // of an error the customer can do nothing about.
              if (await resolveIfSettled()) {
                setSubmitting(false);
                return;
              }
              Alert.alert(
                t('challenge.alreadyDone'),
                err instanceof ApiError ? err.message : t('common.tryAgain')
              );
            } finally {
              setSubmitting(false);
            }
          },
        },
      ]
    );
  };

  if (loading || !step) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.centerText}>Preparing secure verification{'…'}</Text>
      </View>
    );
  }

  const current = step.current_step || 'MPIN';
  const meta = STEP_META[current] || STEP_META.MPIN;
  const stepTitleKey: Record<string, string> = {
    SECURITY_QUESTION: 'challenge.securityQuestion',
    MPIN: 'challenge.mpin',
    OTP: 'challenge.otp',
    ACKNOWLEDGE: 'challenge.acknowledge',
  };
  const isAck = current === 'ACKNOWLEDGE';
  const canSwitch = current !== 'ACKNOWLEDGE';
  const otpExpired = current === 'OTP' && secondsLeft === 0 && !!demoOtp;
  const keyboard = current === 'MPIN' || current === 'OTP' ? 'number-pad' : 'default';

  const shakeStyle = {
    transform: [
      { translateX: shake.interpolate({ inputRange: [-1, 1], outputRange: [-8, 8] }) },
    ],
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Persistent reassurance — the single most important message on this screen */}
      <View style={styles.holdBanner}>
        <Feather name="lock" size={14} color={COLORS.primaryDark} />
        <Text style={styles.holdBannerText}>
          {t('challenge.holdBanner')}
        </Text>
      </View>

      {/* Progress */}
      <View style={styles.progressRow}>
        {step.steps.map((s, i) => (
          <View
            key={s + i}
            style={[
              styles.progressDot,
              i < step.step_number - 1 && styles.progressDone,
              i === step.step_number - 1 && styles.progressActive,
            ]}
          />
        ))}
        <Text style={styles.progressText}>
          Step {step.step_number} of {step.total_steps}
        </Text>
      </View>

      {/* Amount context */}
      <View style={styles.summary}>
        <Text style={styles.summaryText}>
          Verifying investment of{' '}
          <Text style={styles.summaryBold}>{formatCurrency(transactionData.amount)}</Text> in{' '}
          <Text style={styles.summaryBold}>{transactionData.toLabel}</Text>
        </Text>
      </View>

      {/* Step card */}
      <Animated.View style={[styles.card, shakeStyle]}>
        <View style={styles.stepHeader}>
          <View style={styles.stepIconWrap}>
            <Feather name={meta.icon as any} size={22} color={COLORS.primary} />
          </View>
          <View style={styles.flex1}>
            <Text style={styles.stepTitle}>{t(stepTitleKey[current] || 'challenge.mpin')}</Text>
            {step.attempts_left < 3 && (
              <Text style={styles.attemptsText}>
                {step.attempts_left} attempt{step.attempts_left === 1 ? '' : 's'} left
              </Text>
            )}
          </View>
        </View>
        <Text style={styles.prompt}>{step.prompt}</Text>

        {/* Why we asked — reduces the "is this a scam?" reaction that makes
            customers abandon a legitimate step-up. */}
        {whyChallenged ? (
          <View style={styles.whyBox}>
            <Feather name="help-circle" size={13} color={COLORS.primaryDark} />
            <Text style={styles.whyText}>{whyChallenged}</Text>
          </View>
        ) : null}

        {/* Demo OTP helper (hackathon demo — production sends a real SMS) */}
        {current === 'OTP' && demoOtp && (
          <View style={styles.demoOtpBox}>
            <Feather name="message-square" size={14} color={COLORS.primaryDark} />
            <View style={styles.flex1}>
              <Text style={styles.demoOtpText}>
                Demo SMS: your SecureWealth OTP is{' '}
                <Text style={styles.summaryBold}>{demoOtp}</Text>. Never share this OTP
                with anyone.
              </Text>
              <View style={styles.otpMetaRow}>
                <Text style={[styles.otpTimer, otpExpired && { color: COLORS.danger }]}>
                  {otpExpired
                    ? t('challenge.expired')
                    : `${t('challenge.expiresIn')} ${mmss(secondsLeft)}`}
                </Text>
                <TouchableOpacity onPress={resendOtp} activeOpacity={0.7}>
                  <Text style={styles.resendLink}>{t('challenge.resend')}</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        )}

        {!isAck && (
          <TextInput
            style={styles.input}
            value={answer}
            onChangeText={setAnswer}
            keyboardType={keyboard as any}
            secureTextEntry={current === 'MPIN'}
            maxLength={current === 'MPIN' ? 6 : current === 'OTP' ? 6 : 10}
            placeholder={
              current === 'SECURITY_QUESTION'
                ? 'YYYY-MM-DD'
                : current === 'OTP'
                ? '6-digit OTP'
                : '6-digit MPIN'
            }
            placeholderTextColor={COLORS.textTertiary}
            textAlign="center"
            autoCapitalize="none"
          />
        )}

        {notice && !error && (
          <View style={styles.noticeRow}>
            <Feather name="info" size={14} color={COLORS.primaryDark} />
            <Text style={styles.noticeText}>{notice}</Text>
          </View>
        )}

        {error && (
          <View style={styles.errorRow}>
            <Feather name="alert-circle" size={14} color={COLORS.danger} />
            <Text style={styles.errorText}>
              {error} ({step.attempts_left} attempt{step.attempts_left === 1 ? '' : 's'} left)
            </Text>
          </View>
        )}

        <TouchableOpacity
          style={[
            styles.primaryBtn,
            (!isAck && answer.length === 0) || submitting ? styles.btnDisabled : null,
          ]}
          onPress={() => submit(isAck)}
          disabled={(!isAck && answer.length === 0) || submitting}
          activeOpacity={0.85}
        >
          {submitting ? (
            <ActivityIndicator color={COLORS.textOnDark} />
          ) : (
            <>
              <Feather name="shield" size={16} color={COLORS.textOnDark} />
              <Text style={styles.primaryBtnText}>
                {isAck ? 'I Understand — Continue' : 'Verify'}
              </Text>
            </>
          )}
        </TouchableOpacity>

        {/* Task 4.3b — the way out that is NOT a way around */}
        {canSwitch && (
          <TouchableOpacity style={styles.altBtn} onPress={openMethods} activeOpacity={0.7}>
            <Feather name="repeat" size={14} color={COLORS.primary} />
            <Text style={styles.altBtnText}>
              {current === 'OTP'
                ? t('challenge.cantAccessOtp')
                : t('challenge.anotherWay')}
            </Text>
          </TouchableOpacity>
        )}
      </Animated.View>

      {/* Task 4.3c */}
      <TouchableOpacity style={styles.notMeBtn} onPress={notMe} activeOpacity={0.8}>
        <Feather name="shield-off" size={15} color={COLORS.danger} />
        <Text style={styles.notMeText}>{t('challenge.notMe')}</Text>
      </TouchableOpacity>

      <Text style={styles.reassure}>{t('challenge.moneySafe')}</Text>

      {/* ── Method picker sheet ── */}
      <Modal
        visible={methodsOpen}
        transparent
        animationType="slide"
        onRequestClose={() => setMethodsOpen(false)}
      >
        <View style={styles.modalRoot}>
          <View style={styles.sheet}>
            <View style={styles.sheetHead}>
              <Text style={styles.sheetTitle}>{t('challenge.chooseMethod')}</Text>
              <TouchableOpacity
                onPress={() => setMethodsOpen(false)}
                hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
                accessibilityRole="button"
                accessibilityLabel={t('a11y.close')}
              >
                <Feather name="x" size={20} color={COLORS.textSecondary} />
              </TouchableOpacity>
            </View>

            {methodsLoading ? (
              <ActivityIndicator color={COLORS.primary} style={{ marginVertical: SPACING.xl }} />
            ) : (
              <ScrollView>
                {methods.map((m) => {
                  const disabled = !m.available || m.is_current || switching;
                  return (
                    <TouchableOpacity
                      key={m.method}
                      style={[
                        styles.methodCard,
                        m.is_current && styles.methodCardCurrent,
                        !m.available && styles.methodCardOff,
                      ]}
                      onPress={() => chooseMethod(m)}
                      disabled={disabled}
                      activeOpacity={0.8}
                    >
                      <View
                        style={[
                          styles.methodIcon,
                          !m.available && { backgroundColor: COLORS.border },
                        ]}
                      >
                        <Feather
                          name={(METHOD_ICONS[m.method] || 'shield') as any}
                          size={16}
                          color={m.available ? COLORS.primary : COLORS.textTertiary}
                        />
                      </View>
                      <View style={styles.flex1}>
                        <View style={styles.methodTitleRow}>
                          <Text
                            style={[
                              styles.methodLabel,
                              !m.available && { color: COLORS.textTertiary },
                            ]}
                          >
                            {m.label}
                          </Text>
                          {m.is_current && (
                            <View style={styles.currentPill}>
                              <Text style={styles.currentPillText}>CURRENT</Text>
                            </View>
                          )}
                        </View>
                        <Text style={styles.methodDesc}>
                          {m.available ? m.description : m.unavailable_reason}
                        </Text>
                        {m.available && m.extra_step_required && (
                          <Text style={styles.methodWarn}>
                            {t('challenge.extraStep')}
                          </Text>
                        )}
                      </View>
                      {m.available && !m.is_current && (
                        <Feather name="chevron-right" size={18} color={COLORS.textTertiary} />
                      )}
                    </TouchableOpacity>
                  );
                })}
                <Text style={styles.sheetNote}>{methodsNote}</Text>
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: SPACING.lg, paddingBottom: SPACING.xxl },
  flex1: { flex: 1 },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.background,
  },
  centerText: { ...TYPOGRAPHY.body, color: COLORS.textSecondary, marginTop: SPACING.md },

  holdBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    backgroundColor: COLORS.primaryVeryLight,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
  },
  holdBannerText: {
    ...TYPOGRAPHY.caption,
    color: COLORS.primaryDark,
    flex: 1,
    fontWeight: '600',
  },

  progressRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
    marginBottom: SPACING.lg,
  },
  progressDot: { width: 26, height: 6, borderRadius: 3, backgroundColor: COLORS.border },
  progressDone: { backgroundColor: COLORS.success },
  progressActive: { backgroundColor: COLORS.primary },
  progressText: { ...TYPOGRAPHY.caption, color: COLORS.textTertiary, marginLeft: SPACING.sm },

  summary: {
    backgroundColor: COLORS.primaryVeryLight,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
  },
  summaryText: { ...TYPOGRAPHY.body, color: COLORS.primaryDark },
  summaryBold: { fontWeight: '800' },

  card: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: SPACING.lg,
    ...SHADOWS.small,
  },
  stepHeader: { flexDirection: 'row', alignItems: 'center', gap: SPACING.md },
  stepIconWrap: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.primaryVeryLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepTitle: { ...TYPOGRAPHY.h4, color: COLORS.text },
  attemptsText: {
    ...TYPOGRAPHY.caption,
    color: COLORS.warning,
    marginTop: 2,
    fontWeight: '700',
  },
  prompt: {
    ...TYPOGRAPHY.body,
    color: COLORS.textSecondary,
    marginTop: SPACING.md,
    lineHeight: 21,
  },

  whyBox: {
    flexDirection: 'row',
    gap: SPACING.sm,
    backgroundColor: COLORS.primaryVeryLight,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginTop: SPACING.md,
  },
  whyText: { ...TYPOGRAPHY.caption, color: COLORS.primaryDark, flex: 1, lineHeight: 17 },

  demoOtpBox: {
    flexDirection: 'row',
    gap: SPACING.sm,
    backgroundColor: COLORS.primaryVeryLight,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginTop: SPACING.md,
  },
  demoOtpText: { ...TYPOGRAPHY.caption, color: COLORS.primaryDark },
  otpMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: SPACING.sm,
  },
  otpTimer: { ...TYPOGRAPHY.caption, color: COLORS.primaryDark, fontWeight: '700' },
  resendLink: {
    ...TYPOGRAPHY.caption,
    color: COLORS.primary,
    fontWeight: '800',
    textDecorationLine: 'underline',
  },

  input: {
    ...TYPOGRAPHY.h2,
    color: COLORS.text,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.md,
    paddingVertical: SPACING.md,
    marginTop: SPACING.lg,
    letterSpacing: 4,
  },

  noticeRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: SPACING.xs,
    marginTop: SPACING.sm,
  },
  noticeText: { ...TYPOGRAPHY.caption, color: COLORS.primaryDark, flex: 1, lineHeight: 16 },
  errorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
    marginTop: SPACING.sm,
  },
  errorText: { ...TYPOGRAPHY.caption, color: COLORS.danger, flex: 1 },

  primaryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.sm,
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.lg,
    paddingVertical: SPACING.md,
    marginTop: SPACING.lg,
  },
  btnDisabled: { opacity: 0.45 },
  primaryBtnText: { ...TYPOGRAPHY.bodyMedium, color: COLORS.textOnDark, fontSize: 15 },

  altBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.xs,
    paddingVertical: SPACING.md,
    marginTop: SPACING.xs,
  },
  altBtnText: { ...TYPOGRAPHY.caption, color: COLORS.primary, fontWeight: '700' },

  notMeBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.sm,
    borderWidth: 1.5,
    borderColor: COLORS.danger,
    borderRadius: BORDER_RADIUS.lg,
    paddingVertical: SPACING.md,
    marginTop: SPACING.lg,
  },
  notMeText: { ...TYPOGRAPHY.caption, color: COLORS.danger, fontWeight: '800' },

  reassure: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    textAlign: 'center',
    marginTop: SPACING.lg,
    lineHeight: 17,
  },

  // Method sheet
  modalRoot: { flex: 1, backgroundColor: 'rgba(0,0,0,0.45)', justifyContent: 'flex-end' },
  sheet: {
    backgroundColor: COLORS.surface,
    borderTopLeftRadius: BORDER_RADIUS.xl,
    borderTopRightRadius: BORDER_RADIUS.xl,
    padding: SPACING.lg,
    maxHeight: '80%',
  },
  sheetHead: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: SPACING.md,
  },
  sheetTitle: { ...TYPOGRAPHY.h3, color: COLORS.text },
  methodCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.md,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
  },
  methodCardCurrent: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primaryVeryLight,
  },
  methodCardOff: { opacity: 0.6 },
  methodIcon: {
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: COLORS.primaryVeryLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  methodTitleRow: { flexDirection: 'row', alignItems: 'center', gap: SPACING.xs },
  methodLabel: { ...TYPOGRAPHY.bodyMedium, color: COLORS.text },
  currentPill: {
    backgroundColor: COLORS.primary,
    borderRadius: 999,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 2,
  },
  currentPillText: {
    fontSize: 8.5,
    fontWeight: '800',
    color: COLORS.textOnDark,
    letterSpacing: 0.5,
  },
  methodDesc: { ...TYPOGRAPHY.caption, color: COLORS.textTertiary, marginTop: 2, lineHeight: 16 },
  methodWarn: { ...TYPOGRAPHY.caption, color: COLORS.warning, marginTop: 3, fontWeight: '600' },
  sheetNote: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    lineHeight: 16,
    marginTop: SPACING.sm,
    marginBottom: SPACING.lg,
  },
});

export default ChallengeScreen;
