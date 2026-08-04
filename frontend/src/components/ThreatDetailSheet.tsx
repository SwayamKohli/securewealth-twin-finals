// src/components/ThreatDetailSheet.tsx
// ─────────────────────────────────────────────────────────────────────────────
// Threat detail sheet (M6, task 16).
//
// Tapping a flagged message opens this instead of expanding a row inline. A
// scam warning is the one moment where the customer needs the full picture in
// one place: what we saw, why it matters, and — most importantly — what to do
// in the next sixty seconds.
//
// The explanation comes from the live explainability API in the customer's
// chosen language, with the fired signal name as a fallback so the sheet is
// never empty.
// ─────────────────────────────────────────────────────────────────────────────

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Feather } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS } from '../constants/theme';
import { api } from '../api/apiService';
import { useI18n } from '../i18n';

export type ThreatDetail = {
  id: string;
  sender: string;
  text: string;
  suspicious: boolean;
  riskLevel: string;
  score: number;         // 0-1
  topSignal: string | null;
  signals: string[];
};

const humanize = (s: string): string =>
  s.replace(/[_-]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

// What the customer should actually DO. Ordered by urgency, not by severity of
// the signal — the first item is always the one that stops money moving.
const ACTIONS_SUSPICIOUS = [
  {
    icon: 'slash',
    title: 'Do not tap any link in this message',
    detail: 'Scam links copy the bank’s login page to capture your credentials.',
  },
  {
    icon: 'eye-off',
    title: 'Never share an OTP, MPIN or card number',
    detail: 'Punjab & Sind Bank will never ask you for these — not by SMS, call or email.',
  },
  {
    icon: 'phone',
    title: 'If you already replied, call the bank now',
    detail: 'Use the number printed on your card or passbook, not one from the message.',
  },
];

const ACTIONS_SAFE = [
  {
    icon: 'check-circle',
    title: 'Nothing to do',
    detail: 'We found no scam warning signs in this message.',
  },
  {
    icon: 'alert-circle',
    title: 'Still be careful with links',
    detail: 'A safe-looking message can still be forwarded by someone who was scammed.',
  },
];

const ThreatDetailSheet = ({
  threat,
  visible,
  onClose,
  preloaded,
}: {
  threat: ThreatDetail | null;
  visible: boolean;
  onClose: () => void;
  /** Explanation already fetched in the background after the scan. */
  preloaded?: string | null;
}) => {
  const { t, language } = useI18n();
  const [explanation, setExplanation] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [reported, setReported] = useState(false);

  useEffect(() => {
    if (!visible || !threat) return;
    setReported(false);

    // The local model takes several seconds. SmsInboxScan starts fetching the
    // moment a message is flagged, so by the time the customer taps through the
    // text is usually already here — no spinner at all.
    if (preloaded) {
      setExplanation(preloaded);
      setLoading(false);
      return;
    }
    setExplanation(null);
    setLoading(true);
    api
      .explainPhishing({
        scan_result: {
          risk_level: threat.riskLevel,
          top_signal: threat.topSignal,
          phishing_score: threat.score,
        },
        language,
      })
      .then((res) => setExplanation(res?.explanation || null))
      .catch(() => setExplanation(null))
      .finally(() => setLoading(false));
  }, [visible, threat, language, preloaded]);

  if (!threat) return null;

  const actions = threat.suspicious ? ACTIONS_SUSPICIOUS : ACTIONS_SAFE;
  const accent = threat.suspicious ? '#DC2626' : COLORS.success;
  const fallback = threat.topSignal
    ? `We flagged this because of: ${humanize(threat.topSignal).toLowerCase()}.`
    : 'We found several patterns commonly used in scam messages.';

  const report = () => {
    // Honest scope: this records the customer's judgement locally for the
    // session. A production build would POST it to the bank's fraud desk to
    // improve the shared signal set.
    setReported(true);
    Alert.alert(
      'Thank you for reporting',
      'We have noted this message as a scam. Never reply to it, and delete it when you can.'
    );
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.root}>
        <View style={styles.sheet}>
          <View style={styles.handle} />

          <View style={styles.head}>
            <View style={[styles.headIcon, { backgroundColor: accent + '18' }]}>
              <Feather
                name={threat.suspicious ? 'alert-triangle' : 'check-circle'}
                size={20}
                color={accent}
              />
            </View>
            <View style={styles.flex1}>
              <Text style={[styles.headTitle, { color: accent }]}>
                {threat.suspicious ? t('phishing.likelyScam') : t('phishing.safe')}
              </Text>
              <Text style={styles.headSub}>
                From {threat.sender} · {Math.round(threat.score * 100)}% risk
              </Text>
            </View>
            <TouchableOpacity
              onPress={onClose}
              hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
              accessibilityRole="button"
              accessibilityLabel={t('a11y.close')}
            >
              <Feather name="x" size={20} color={COLORS.textSecondary} />
            </TouchableOpacity>
          </View>

          <ScrollView showsVerticalScrollIndicator={false}>
            <View style={styles.messageBox}>
              <Text style={styles.messageText}>{threat.text}</Text>
            </View>

            <Text style={styles.sectionLabel}>{t('phishing.whyFlagged')}</Text>
            {loading ? (
              <View style={styles.loadingRow}>
                <ActivityIndicator color={COLORS.primary} size="small" />
                <Text style={styles.loadingText}>
                  Writing a plain-language explanation{'\u2026'}
                </Text>
              </View>
            ) : (
              <Text style={styles.explanation}>{explanation || fallback}</Text>
            )}

            {threat.signals.length > 0 && (
              <View style={styles.signalWrap}>
                {threat.signals.map((sig) => (
                  <View key={sig} style={styles.signalChip}>
                    <Text style={styles.signalChipText}>{humanize(sig)}</Text>
                  </View>
                ))}
              </View>
            )}

            <Text style={styles.sectionLabel}>{t('phishing.whatToDo')}</Text>
            {actions.map((a, i) => (
              <View key={a.title} style={styles.actionRow}>
                <View style={styles.actionIndex}>
                  <Text style={styles.actionIndexText}>{i + 1}</Text>
                </View>
                <View style={styles.flex1}>
                  <Text style={styles.actionTitle}>{a.title}</Text>
                  <Text style={styles.actionDetail}>{a.detail}</Text>
                </View>
              </View>
            ))}

            {threat.suspicious && (
              <TouchableOpacity
                style={[styles.reportBtn, reported && styles.reportBtnDone]}
                onPress={report}
                disabled={reported}
                activeOpacity={0.85}
              >
                <Feather
                  name={reported ? 'check' : 'flag'}
                  size={15}
                  color={reported ? COLORS.success : COLORS.textOnDark}
                />
                <Text style={[styles.reportBtnText, reported && { color: COLORS.success }]}>
                  {reported ? t('common.done') : t('phishing.reportScam')}
                </Text>
              </TouchableOpacity>
            )}

            <View style={{ height: SPACING.xl }} />
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: 'rgba(0,0,0,0.45)', justifyContent: 'flex-end' },
  sheet: {
    backgroundColor: COLORS.surface,
    borderTopLeftRadius: BORDER_RADIUS.xl,
    borderTopRightRadius: BORDER_RADIUS.xl,
    paddingHorizontal: SPACING.lg,
    paddingTop: SPACING.sm,
    maxHeight: '88%',
  },
  handle: {
    width: 38,
    height: 4,
    borderRadius: 2,
    backgroundColor: COLORS.border,
    alignSelf: 'center',
    marginBottom: SPACING.md,
  },
  flex1: { flex: 1 },

  head: { flexDirection: 'row', alignItems: 'center', gap: SPACING.md, marginBottom: SPACING.md },
  headIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headTitle: { ...TYPOGRAPHY.h3 },
  headSub: { ...TYPOGRAPHY.caption, color: COLORS.textTertiary, marginTop: 1 },

  messageBox: {
    backgroundColor: COLORS.background,
    borderRadius: BORDER_RADIUS.md,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: SPACING.md,
  },
  messageText: { ...TYPOGRAPHY.bodySm, color: COLORS.text, lineHeight: 19 },

  sectionLabel: {
    ...TYPOGRAPHY.captionBold,
    color: COLORS.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.7,
    marginTop: SPACING.lg,
    marginBottom: SPACING.xs,
  },
  explanation: { ...TYPOGRAPHY.body, color: COLORS.textSecondary, lineHeight: 21 },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginVertical: SPACING.sm,
  },
  loadingText: { ...TYPOGRAPHY.caption, color: COLORS.textTertiary },

  signalWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: SPACING.xs, marginTop: SPACING.sm },
  signalChip: {
    backgroundColor: COLORS.primaryVeryLight,
    borderRadius: 999,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 3,
  },
  signalChipText: { ...TYPOGRAPHY.caption, color: COLORS.primaryDark, fontWeight: '600' },

  actionRow: {
    flexDirection: 'row',
    gap: SPACING.md,
    alignItems: 'flex-start',
    marginTop: SPACING.md,
  },
  actionIndex: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionIndexText: { fontSize: 11, fontWeight: '800', color: COLORS.textOnDark },
  actionTitle: { ...TYPOGRAPHY.bodyMedium, color: COLORS.text },
  actionDetail: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    marginTop: 2,
    lineHeight: 16,
  },

  reportBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.sm,
    backgroundColor: '#DC2626',
    borderRadius: BORDER_RADIUS.lg,
    paddingVertical: SPACING.md,
    marginTop: SPACING.xl,
  },
  reportBtnDone: {
    backgroundColor: COLORS.surface,
    borderWidth: 1.5,
    borderColor: COLORS.success,
  },
  reportBtnText: { ...TYPOGRAPHY.bodyMedium, color: COLORS.textOnDark, fontWeight: '700' },
});

export default ThreatDetailSheet;
