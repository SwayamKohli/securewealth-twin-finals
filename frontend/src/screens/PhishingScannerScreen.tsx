// src/screens/PhishingScannerScreen.tsx
// SecureWealth Twin — Check a Message
//
// BACKEND INTEGRATION (was local analyzeMessage() only):
//  • handleScan now calls POST /phishing/scan and maps the backend's
//    phishing_score + risk_level (SAFE/LOW/MEDIUM/HIGH) + fired_signals into the
//    existing 3-way UI status (SAFE / SUSPICIOUS / PHISHING) + signal IDs.
//  • Falls back to the local analyzeMessage() if the API is unreachable, so the
//    demo still works offline.
//  • fired_signals from the backend are matched to the local signalDefs keys so
//    the "What We Found" cards keep rendering. Unknown signal keys are ignored.
//  • UI phases, animation, PHISHING_STYLES, and styles are unchanged.

import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Animated,
  Easing,
  Alert,
} from 'react-native';
import { Feather } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS, PHISHING_STYLES } from '../constants/theme';
import { analyzeMessage, PhishingAssessment, PhishingClass } from '../utils/phishingAnalyzer';
import phishingSignalsData from '../../mockData/phishing_signals.json';
import { api } from '../api/apiService';
import type { PhishingScanResponse } from '../api/types';

// ── Types ─────────────────────────────────────────────────────────────────────
type Phase = 'idle' | 'scanning' | 'result';

const signalDefs = phishingSignalsData.signalDefinitions as Record<
  string,
  { friendlyName: string; explanation: string; icon: string }
>;

// Cycling messages during the scanning phase
const SCAN_STEPS = [
  'Reading the message\u2026',
  'Checking for suspicious links\u2026',
  'Comparing with known scam patterns\u2026',
  'Putting together our answer\u2026',
];

// "What should I do?" guidance per result status
const ACTION_STEPS: Record<string, string[]> = {
  SAFE: [
    'This message looks fine — no action needed.',
    'Still unsure? Call us using the number on the back of your card, never a number from the message.',
  ],
  SUSPICIOUS: [
    "Don't click any links or reply to this message.",
    'Contact us only through our official app or the number on your card.',
    "Once you're sure, you can delete the message.",
  ],
  PHISHING: [
    'Do not click any links or reply.',
    'Never share your OTP, PIN, password, or card details — we will never ask for these.',
    'Report this message using the button below, then delete it.',
  ],
};

// ── Backend → UI mapping ──────────────────────────────────────────────────────
// The backend risk_level is SAFE/LOW/MEDIUM/HIGH; the UI has 3 buckets.
//   HIGH            → PHISHING
//   MEDIUM | LOW    → SUSPICIOUS
//   SAFE            → SAFE
// We also cross-check phishing_score as a fallback if risk_level is missing.
const mapRiskLevel = (res: PhishingScanResponse): PhishingClass => {
  const level = String(res?.risk_level || '').toUpperCase();
  if (level === 'HIGH') return 'PHISHING';
  if (level === 'MEDIUM' || level === 'LOW') return 'SUSPICIOUS';
  if (level === 'SAFE') return 'SAFE';
  // Fallback: derive from numeric score if risk_level is absent/unknown.
  const score = Number(res?.phishing_score) || 0;
  if (score >= 0.7) return 'PHISHING';
  if (score >= 0.3) return 'SUSPICIOUS';
  return 'SAFE';
};

// Match backend fired_signals to local signalDefs keys (case-insensitive).
// The backend may use different casing or extra signals; we keep only those we
// can render, so the "What We Found" section stays meaningful.
const mapSignals = (res: PhishingScanResponse): string[] => {
  const fired = Array.isArray(res?.fired_signals) ? res.fired_signals : [];
  const defKeys = Object.keys(signalDefs);
  const matched: string[] = [];
  for (const raw of fired) {
    const key = String(raw).toUpperCase();
    const hit = defKeys.find((k) => k.toUpperCase() === key);
    if (hit && !matched.includes(hit)) matched.push(hit);
  }
  return matched;
};

// ── Sub-components ────────────────────────────────────────────────────────────

// Animated magnifier shown during the scanning phase
const ScanningView = () => {
  const pulseAnim = useRef(new Animated.Value(0)).current;
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 700,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 0,
          duration: 700,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    ).start();

    const interval = setInterval(() => {
      setStepIndex((i) => (i + 1) % SCAN_STEPS.length);
    }, 400);
    return () => clearInterval(interval);
  }, []);

  const scale = pulseAnim.interpolate({ inputRange: [0, 1], outputRange: [1, 1.12] });

  return (
    <View style={styles.scanningContainer}>
      <Animated.View style={[styles.scanningIconWrap, { transform: [{ scale }] }]}>
        <Feather name="search" size={48} color={COLORS.primary} />
      </Animated.View>
      <Text style={styles.scanningTitle}>Checking this message</Text>
      <Text style={styles.scanningStep}>{SCAN_STEPS[stepIndex]}</Text>
    </View>
  );
};

// Collapsible "what we found" signal row
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

  return (
    <TouchableOpacity style={styles.signalRow} onPress={onToggle} activeOpacity={0.7}>
      <View style={styles.signalRowHeader}>
        <View style={styles.signalIconWrap}>
          <Feather name={def.icon as any} size={16} color={COLORS.danger} />
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
const PhishingScannerScreen = () => {
  const [inputText, setInputText] = useState('');
  const [phase, setPhase] = useState<Phase>('idle');
  const [result, setResult] = useState<PhishingAssessment | null>(null);
  const [expandedSignal, setExpandedSignal] = useState<string | null>(null);

  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(12)).current;

  const handleExampleTap = (text: string) => {
    setInputText(text);
    setPhase('idle');
    setResult(null);
  };

  const revealResult = (assessment: PhishingAssessment) => {
    setResult(assessment);
    setPhase('result');

    fadeAnim.setValue(0);
    slideAnim.setValue(12);
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

  const handleScan = async () => {
    if (!inputText.trim()) {
      Alert.alert('Add a message', 'Paste or type a message or link to check first.');
      return;
    }

    setPhase('scanning');
    setResult(null);
    setExpandedSignal(null);

    const startedAt = Date.now();
    const MIN_SCAN_MS = 1400; // keep the reassuring animation duration
    const finish = (assessment: PhishingAssessment) => {
      const wait = Math.max(0, MIN_SCAN_MS - (Date.now() - startedAt));
      setTimeout(() => revealResult(assessment), wait);
    };

    try {
      const res = await api.scanPhishing({ message: inputText.trim() });
      finish({ status: mapRiskLevel(res), signalIds: mapSignals(res) });
    } catch (e) {
      // Offline / API failure → deterministic local analysis so the demo continues.
      finish(analyzeMessage(inputText));
    }
  };

  const handleReset = () => {
    setInputText('');
    setResult(null);
    setPhase('idle');
    setExpandedSignal(null);
  };

  const handleReport = () => {
    Alert.alert(
      'Thanks for reporting',
      "We've noted this message. Our security team uses reports like this to help protect everyone."
    );
  };

  const phishingStyle = result ? PHISHING_STYLES[result.status] : null;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
      keyboardShouldPersistTaps="handled"
    >
      {/* ── Intro ── */}
      <View style={styles.introCard}>
        <Text style={styles.introTitle}>What would you like to check?</Text>
        <Text style={styles.introSubtitle}>
          Paste a suspicious text message, email, or link below — we'll check it for
          common scam warning signs.
        </Text>

        {/* Example chips */}
        <Text style={styles.exampleLabel}>Try an example</Text>
        <View style={styles.exampleRow}>
          {phishingSignalsData.exampleMessages.map((ex) => (
            <TouchableOpacity
              key={ex.id}
              style={styles.exampleChip}
              onPress={() => handleExampleTap(ex.text)}
              activeOpacity={0.7}
            >
              <Text style={styles.exampleChipText}>{ex.label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Input */}
        <TextInput
          style={styles.textInput}
          placeholder="Paste the message or link here..."
          placeholderTextColor={COLORS.textTertiary}
          value={inputText}
          onChangeText={(text) => {
            setInputText(text);
            if (phase === 'result') {
              setPhase('idle');
              setResult(null);
            }
          }}
          multiline
          textAlignVertical="top"
        />

        <TouchableOpacity
          style={[styles.scanBtn, !inputText.trim() && styles.scanBtnDisabled]}
          onPress={handleScan}
          disabled={!inputText.trim() || phase === 'scanning'}
          activeOpacity={0.8}
        >
          <Feather name="search" size={18} color={COLORS.textOnDark} />
          <Text style={styles.scanBtnText}>Check This Message</Text>
        </TouchableOpacity>
      </View>

      {/* ── Scanning phase ── */}
      {phase === 'scanning' && <ScanningView />}

      {/* ── Result phase ── */}
      {phase === 'result' && result && phishingStyle && (
        <Animated.View style={{ opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}>
          {/* Result header */}
          <View style={[styles.resultCard, { backgroundColor: phishingStyle.bgColor }]}>
            <View style={styles.resultHeader}>
              <Feather name={phishingStyle.icon as any} size={32} color={phishingStyle.color} />
              <View style={styles.resultHeaderText}>
                <Text style={[styles.resultLabel, { color: phishingStyle.color }]}>
                  {phishingStyle.label}
                </Text>
                <Text style={styles.resultSublabel}>{phishingStyle.sublabel}</Text>
              </View>
            </View>
          </View>

          {/* What we found */}
          {result.signalIds.length > 0 && (
            <View style={styles.card}>
              <Text style={styles.cardTitle}>What We Found</Text>
              {result.signalIds.map((id) => (
                <SignalRow
                  key={id}
                  signalId={id}
                  expanded={expandedSignal === id}
                  onToggle={() => setExpandedSignal((prev) => (prev === id ? null : id))}
                />
              ))}
            </View>
          )}

          {/* What should I do */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>What Should I Do?</Text>
            {ACTION_STEPS[result.status].map((step, i) => (
              <View key={i} style={styles.actionStepRow}>
                <View style={styles.actionStepNumber}>
                  <Text style={styles.actionStepNumberText}>{i + 1}</Text>
                </View>
                <Text style={styles.actionStepText}>{step}</Text>
              </View>
            ))}
          </View>

          {/* Actions */}
          <View style={styles.actions}>
            {(result.status === 'SUSPICIOUS' || result.status === 'PHISHING') && (
              <TouchableOpacity style={styles.reportBtn} onPress={handleReport} activeOpacity={0.8}>
                <Feather name="flag" size={16} color={COLORS.danger} />
                <Text style={styles.reportBtnText}>Report This Message</Text>
              </TouchableOpacity>
            )}
            <TouchableOpacity style={styles.resetBtn} onPress={handleReset} activeOpacity={0.8}>
              <Feather name="refresh-cw" size={16} color={COLORS.primary} />
              <Text style={styles.resetBtnText}>Check Another Message</Text>
            </TouchableOpacity>
          </View>
        </Animated.View>
      )}

      {/* ── Static reference card (always visible) ── */}
      <View style={styles.referenceCard}>
        <Text style={styles.cardTitle}>Common Warning Signs</Text>
        <Text style={styles.referenceSubtitle}>
          Genuine messages from PSB will never do these things:
        </Text>
        {Object.entries(signalDefs).map(([id, def]) => (
          <View key={id} style={styles.referenceRow}>
            <View style={styles.referenceIconWrap}>
              <Feather name={def.icon as any} size={14} color={COLORS.textSecondary} />
            </View>
            <Text style={styles.referenceText}>{def.friendlyName}</Text>
          </View>
        ))}
      </View>

      <View style={{ height: SPACING.xxl }} />
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

  // Intro card
  introCard: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    marginBottom: SPACING.md,
    ...SHADOWS.small,
  },
  introTitle: {
    ...TYPOGRAPHY.h4,
    color: COLORS.text,
    fontWeight: '700',
    marginBottom: SPACING.xs,
  },
  introSubtitle: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    lineHeight: 20,
    marginBottom: SPACING.md,
  },
  exampleLabel: {
    ...TYPOGRAPHY.label,
    color: COLORS.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: SPACING.sm,
  },
  exampleRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
    marginBottom: SPACING.md,
  },
  exampleChip: {
    backgroundColor: COLORS.primaryVeryLight,
    borderRadius: BORDER_RADIUS.full,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.xs,
    borderWidth: 1,
    borderColor: COLORS.primary + '20',
  },
  exampleChipText: {
    ...TYPOGRAPHY.caption,
    color: COLORS.primaryMedium,
    fontWeight: '600',
  },

  // Input
  textInput: {
    backgroundColor: COLORS.surfaceLight,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.lg,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.md,
    ...TYPOGRAPHY.bodySm,
    color: COLORS.text,
    minHeight: 110,
    marginBottom: SPACING.md,
  },
  scanBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.lg,
    paddingVertical: SPACING.md,
    gap: SPACING.sm,
  },
  scanBtnDisabled: {
    backgroundColor: COLORS.borderDark,
  },
  scanBtnText: {
    ...TYPOGRAPHY.button,
    color: COLORS.textOnDark,
  },

  // Scanning phase
  scanningContainer: {
    alignItems: 'center',
    paddingVertical: SPACING.xxl,
  },
  scanningIconWrap: {
    width: 88,
    height: 88,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.primaryVeryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.lg,
  },
  scanningTitle: {
    ...TYPOGRAPHY.h4,
    color: COLORS.text,
    fontWeight: '700',
    marginBottom: SPACING.xs,
  },
  scanningStep: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
  },

  // Result header card
  resultCard: {
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    marginBottom: SPACING.md,
  },
  resultHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.md,
  },
  resultHeaderText: {
    flex: 1,
  },
  resultLabel: {
    ...TYPOGRAPHY.h4,
    fontWeight: '700',
    marginBottom: 2,
  },
  resultSublabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    lineHeight: 19,
  },

  // Generic card
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

  // Signal row (What We Found)
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
    backgroundColor: COLORS.dangerLight,
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

  // Action steps
  actionStepRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: SPACING.sm,
    marginBottom: SPACING.sm,
  },
  actionStepNumber: {
    width: 22,
    height: 22,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.primaryVeryLight,
    justifyContent: 'center',
    alignItems: 'center',
    flexShrink: 0,
    marginTop: 1,
  },
  actionStepNumberText: {
    ...TYPOGRAPHY.captionBold,
    color: COLORS.primaryMedium,
  },
  actionStepText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.text,
    flex: 1,
    lineHeight: 20,
  },

  // Actions
  actions: {
    gap: SPACING.sm,
    marginBottom: SPACING.md,
  },
  reportBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.dangerLight,
    borderRadius: BORDER_RADIUS.lg,
    paddingVertical: SPACING.md,
    gap: SPACING.sm,
  },
  reportBtnText: {
    ...TYPOGRAPHY.button,
    color: COLORS.danger,
  },
  resetBtn: {
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
  resetBtnText: {
    ...TYPOGRAPHY.button,
    color: COLORS.primary,
  },

  // Reference card
  referenceCard: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    ...SHADOWS.small,
  },
  referenceSubtitle: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginBottom: SPACING.md,
  },
  referenceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginBottom: SPACING.sm,
  },
  referenceIconWrap: {
    width: 28,
    height: 28,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.surfaceLight,
    justifyContent: 'center',
    alignItems: 'center',
  },
  referenceText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    flex: 1,
  },
});

export default PhishingScannerScreen;