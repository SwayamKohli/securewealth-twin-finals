// src/components/SmsInboxScan.tsx
// SecureWealth Twin — Automatic SMS Phishing Scan (task 6)
//
// Flow: Permission → SMS access → Recent messages → Backend bulk scan →
//       Risk result → Explanation → Alert.
//
// WHAT IS REAL: every verdict, score and signal shown here comes from the
// live backend phishing engine (POST /phishing/bulk-scan) and the live
// explainability API — nothing is hard-coded.
//
// WHAT IS SIMULATED: the message list itself. Expo Go cannot read the OS SMS
// inbox (iOS forbids it entirely; Android needs a native build with
// READ_SMS). On a native build, replace readInbox() below with the native
// SMS reader — the rest of this component needs no changes.

import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS } from '../constants/theme';
import { api } from '../api/apiService';
import { useI18n } from '../i18n';
import type { PhishingScanResponse } from '../api/types';
import ThreatDetailSheet, { type ThreatDetail } from './ThreatDetailSheet';

const CONSENT_KEY = 'swt_sms_scan_consent';

// ── Simulated recent SMS inbox (scanned by the REAL backend engine) ───────────
interface DemoSms {
  id: string;
  sender: string;
  text: string;
}

const DEMO_INBOX: DemoSms[] = [
  {
    id: 's1',
    sender: 'SBIBNK',
    text: 'Rs 4,000 debited from A/c XX4821 for Bluechip Equity Fund SIP. Avl bal: Rs 2,46,000. If not you, call 1800-11-2211.',
  },
  {
    id: 's2',
    sender: 'SWLTH',
    text: 'Your SecureWealth OTP is 482913. It is valid for 5 minutes. Never share this OTP with anyone.',
  },
  {
    id: 's3',
    sender: '+91-98XXXXXX01',
    text: 'URGENT: Your bank account will be BLOCKED today! Update KYC immediately at http://sbi-kyc-verify.xyz or lose access.',
  },
  {
    id: 's4',
    sender: 'VM-REWRD',
    text: 'Congratulations! You have WON Rs 25,00,000 in the RBI Lucky Draw. Share your OTP and account number to claim now.',
  },
  {
    id: 's5',
    sender: 'AD-DLVRY',
    text: 'Your parcel is on hold. Pay Rs 25 customs fee at http://indiapost-track.club to release delivery.',
  },
  {
    id: 's6',
    sender: 'Mom',
    text: 'Beta, dinner at 8. Call me when you leave office.',
  },
];

const OTP_REGEX = /\b(otp|one[\s-]?time\s?password)\b/i;

type Verdict = 'SAFE' | 'SUSPICIOUS';

interface ScanRow {
  sms: DemoSms;
  verdict: Verdict;
  riskLevel: string;
  topSignal: string | null;
  score: number;
  signals: string[];      // live signal groups returned by the engine
  signalCount: number;
  isOtpMessage: boolean;
}

/** Swap this for the native SMS reader in a development build. */
const readInbox = async (): Promise<DemoSms[]> => DEMO_INBOX;

const verdictFrom = (r: PhishingScanResponse): Verdict =>
  String(r.risk_level).toUpperCase() === 'SAFE' ||
  String(r.risk_level).toUpperCase() === 'LOW'
    ? 'SAFE'
    : 'SUSPICIOUS';

const humanizeSignal = (s: string | null): string =>
  s ? s.replace(/[_-]+/g, ' ').toLowerCase() : '';

export type ScanSummary = {
  scanned: number;
  threats: number;
  scannedAt: Date | null;
  consent: boolean;
};

const SmsInboxScan = ({ onSummary }: { onSummary?: (s: ScanSummary) => void }) => {
  const { t, language } = useI18n();
  const [consent, setConsent] = useState<boolean | null>(null);
  const [scanning, setScanning] = useState(false);
  const [rows, setRows] = useState<ScanRow[] | null>(null);
  const [scannedAt, setScannedAt] = useState<Date | null>(null);
  // Task 16 — a flagged message opens the full detail sheet rather than a
  // cramped inline expansion.
  const [activeThreat, setActiveThreat] = useState<ThreatDetail | null>(null);
  // Explanations fetched in the background so the detail sheet opens instantly.
  const [preloaded, setPreloaded] = useState<Record<string, string>>({});

  useEffect(() => {
    AsyncStorage.getItem(CONSENT_KEY).then((v) => setConsent(v === 'yes'));
  }, []);

  const runScan = useCallback(async () => {
    setScanning(true);
    try {
      const inbox = await readInbox();
      const results = await api.bulkScanPhishing({
        messages: inbox.map((m) => ({ message: m.text })),
      });
      setScannedAt(new Date());
      const mapped: ScanRow[] = inbox.map((sms, i) => {
        const r = results[i];
        return {
          sms,
          verdict: r ? verdictFrom(r) : 'SAFE',
          riskLevel: r ? String(r.risk_level) : 'SAFE',
          topSignal: r?.top_signal ?? null,
          score: r ? Number(r.phishing_score) || 0 : 0,
          signals: (r?.signal_groups_fired as string[]) || [],
          signalCount: r?.signal_count ?? 0,
          isOtpMessage: OTP_REGEX.test(sms.text),
        };
      });
      setRows(mapped);

      // Warm the explanations for anything flagged. Sequential rather than
      // parallel: the local model handles one request at a time, and firing
      // several at once only makes the first one slower.
      (async () => {
        for (const row of mapped.filter((r) => r.verdict === 'SUSPICIOUS')) {
          try {
            const res = await api.explainPhishing({
              scan_result: {
                risk_level: row.riskLevel,
                top_signal: row.topSignal,
                phishing_score: row.score,
              },
              language,
            });
            if (res?.explanation) {
              setPreloaded((prev) => ({ ...prev, [row.sms.id]: res.explanation }));
            }
          } catch {
            // Sheet falls back to fetching on open, then to the signal name.
          }
        }
      })();
    } catch {
      setRows(null);
    } finally {
      setScanning(false);
    }
  }, [language]);

  // Keep the protection header in sync with what the scan actually found.
  useEffect(() => {
    onSummary?.({
      scanned: rows?.length ?? 0,
      threats: (rows || []).filter((r) => r.verdict === 'SUSPICIOUS').length,
      scannedAt,
      consent: consent === true,
    });
  }, [rows, scannedAt, consent, onSummary]);

  // Automatic scan once consent is granted (task 6 — no manual upload)
  useEffect(() => {
    if (consent === true && rows === null && !scanning) runScan();
  }, [consent, rows, scanning, runScan]);

  const grantConsent = async () => {
    await AsyncStorage.setItem(CONSENT_KEY, 'yes');
    setConsent(true);
  };

  const revokeConsent = async () => {
    await AsyncStorage.setItem(CONSENT_KEY, 'no');
    setConsent(false);
    setRows(null);
  };

  // NOTE: the old inline toggleExplain() was removed in M6 — the explanation
  // now lives in ThreatDetailSheet, alongside the actions the customer should
  // take. Fetching it there keeps one code path for "why was this flagged".

  if (consent === null) return null;

  // ── Consent card ──
  if (!consent) {
    return (
      <View style={styles.card}>
        <View style={styles.headerRow}>
          <View style={styles.iconWrap}>
            <Feather name="message-square" size={20} color={COLORS.primary} />
          </View>
          <View style={styles.flex1}>
            <Text style={styles.title}>{t('phishing.autoTitle')}</Text>
            <Text style={styles.subtitle}>
              With your permission, we scan your recent messages for scams and
              phishing — automatically, in the background.
            </Text>
          </View>
        </View>
        <View style={styles.consentPoints}>
          <Text style={styles.point}>• Messages are analysed for scam patterns only</Text>
          <Text style={styles.point}>• Nothing is stored or shared</Text>
          <Text style={styles.point}>• You can turn this off any time</Text>
        </View>
        <TouchableOpacity style={styles.primaryBtn} onPress={grantConsent} activeOpacity={0.85}>
          <Feather name="shield" size={16} color={COLORS.textOnDark} />
          <Text style={styles.primaryBtnText}>{t('phishing.allowScan')}</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // ── Scan results ──
  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <View style={styles.iconWrap}>
          <Feather name="inbox" size={20} color={COLORS.primary} />
        </View>
        <View style={styles.flex1}>
          <Text style={styles.title}>{t('phishing.autoScanTitle')}</Text>
          <Text style={styles.subtitle}>
            {scannedAt
              ? t('phishing.scannedAt')
                  .replace('{n}', String(rows?.length ?? 0))
                  .replace(
                    '{time}',
                    scannedAt.toLocaleTimeString('en-IN', { hour12: true })
                  )
              : t('phishing.scanning')}
          </Text>
        </View>
        {scanning ? (
          <ActivityIndicator color={COLORS.primary} />
        ) : (
          <TouchableOpacity
            onPress={runScan}
            activeOpacity={0.7}
            hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
            accessibilityRole="button"
            accessibilityLabel={t('a11y.refreshScan')}
          >
            <Feather name="refresh-cw" size={18} color={COLORS.primary} />
          </TouchableOpacity>
        )}
      </View>

      {rows === null && !scanning && (
        <Text style={styles.subtitle}>
          {t('phishing.scanUnavail')}
        </Text>
      )}

      {rows?.map((row) => {
        const suspicious = row.verdict === 'SUSPICIOUS';
        return (
          <TouchableOpacity
            key={row.sms.id}
            style={styles.smsRow}
            onPress={() =>
              setActiveThreat({
                id: row.sms.id,
                sender: row.sms.sender,
                text: row.sms.text,
                suspicious,
                riskLevel: row.riskLevel,
                score: row.score,
                topSignal: row.topSignal,
                signals: row.signals,
              })
            }
            activeOpacity={0.75}
          >
            <View style={styles.smsHeader}>
              <Text style={styles.sender}>{row.sms.sender}</Text>
              <View
                style={[
                  styles.pill,
                  { backgroundColor: suspicious ? '#FEE2E2' : '#DCFCE7' },
                ]}
              >
                <Feather
                  name={suspicious ? 'alert-triangle' : 'check-circle'}
                  size={11}
                  color={suspicious ? '#DC2626' : '#16A34A'}
                />
                <Text
                  style={[
                    styles.pillText,
                    { color: suspicious ? '#DC2626' : '#16A34A' },
                  ]}
                >
                  {suspicious ? t('phishing.suspicious') : t('phishing.safe')}
                </Text>
              </View>
            </View>
            <Text style={styles.smsText} numberOfLines={2}>
              {row.sms.text}
            </Text>

            {/* Live engine output — proves this is a real scan, not a canned label */}
            <View style={styles.scoreRow}>
              <View style={styles.scoreBar}>
                <View
                  style={[
                    styles.scoreFill,
                    {
                      width: `${Math.round(row.score * 100)}%`,
                      backgroundColor: suspicious ? '#DC2626' : COLORS.success,
                    },
                  ]}
                />
              </View>
              <Text style={styles.scoreText}>
                {Math.round(row.score * 100)}% risk {'\u00B7'} {row.riskLevel}
              </Text>
            </View>
            {row.signals.length > 0 && (
              <View style={styles.chipRow}>
                {row.signals.slice(0, 3).map((sig) => (
                  <View key={sig} style={styles.signalChip}>
                    <Text style={styles.signalChipText}>{humanizeSignal(sig)}</Text>
                  </View>
                ))}
                {row.signalCount > 3 && (
                  <Text style={styles.moreSignals}>+{row.signalCount - 3} more</Text>
                )}
              </View>
            )}

            {/* OTP message → mandatory warning (task 6) */}
            {row.isOtpMessage && !suspicious && (
              <View style={styles.otpWarn}>
                <Feather name="lock" size={12} color={COLORS.primaryDark} />
                <Text style={styles.otpWarnText}>{t('challenge.otpNeverShare')}</Text>
              </View>
            )}

            <View style={styles.tapHintRow}>
              <Text style={styles.tapHint}>
                {suspicious ? 'Tap to see why and what to do' : 'Tap for details'}
              </Text>
              <Feather name="chevron-right" size={14} color={COLORS.textTertiary} />
            </View>
          </TouchableOpacity>
        );
      })}

      <TouchableOpacity onPress={revokeConsent} activeOpacity={0.7}>
        <Text style={styles.revoke}>{t('phishing.turnOff')}</Text>
      </TouchableOpacity>

      <ThreatDetailSheet
        threat={activeThreat}
        visible={!!activeThreat}
        onClose={() => setActiveThreat(null)}
        preloaded={activeThreat ? preloaded[activeThreat.id] : null}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: SPACING.lg,
    marginBottom: SPACING.lg,
  },
  flex1: { flex: 1 },
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: SPACING.md },
  iconWrap: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.primaryVeryLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: { ...TYPOGRAPHY.bodyMedium, color: COLORS.text, fontWeight: '700' },
  subtitle: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary, marginTop: 2 },
  consentPoints: { marginTop: SPACING.md, gap: 4 },
  point: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary },
  primaryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.sm,
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.md,
    paddingVertical: SPACING.md,
    marginTop: SPACING.md,
  },
  primaryBtnText: { ...TYPOGRAPHY.bodyMedium, color: COLORS.textOnDark },

  smsRow: {
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    paddingVertical: SPACING.md,
  },
  smsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  sender: { ...TYPOGRAPHY.captionBold, color: COLORS.text },
  pill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 3,
    borderRadius: 999,
  },
  pillText: { fontSize: 10, fontWeight: '800' },
  smsText: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary, lineHeight: 17 },

  scoreRow: { flexDirection: 'row', alignItems: 'center', gap: SPACING.sm, marginTop: SPACING.sm },
  scoreBar: {
    flex: 1, height: 5, borderRadius: 3,
    backgroundColor: COLORS.border, overflow: 'hidden',
  },
  scoreFill: { height: '100%', borderRadius: 3 },
  scoreText: { fontSize: 10.5, color: COLORS.textTertiary, fontWeight: '700' },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 5, marginTop: SPACING.xs },
  signalChip: {
    backgroundColor: COLORS.border,
    borderRadius: 999, paddingHorizontal: SPACING.sm, paddingVertical: 2,
  },
  signalChipText: { fontSize: 9.5, color: COLORS.textSecondary, fontWeight: '600' },
  moreSignals: { fontSize: 9.5, color: COLORS.textTertiary, alignSelf: 'center' },

  otpWarn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
    backgroundColor: COLORS.primaryVeryLight,
    borderRadius: BORDER_RADIUS.sm,
    padding: SPACING.sm,
    marginTop: SPACING.sm,
  },
  otpWarnText: { ...TYPOGRAPHY.caption, color: COLORS.primaryDark, flex: 1 },


  tapHintRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: 2,
    marginTop: SPACING.sm,
  },
  tapHint: { ...TYPOGRAPHY.caption, color: COLORS.textTertiary, fontWeight: '600' },
  revoke: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    textAlign: 'center',
    marginTop: SPACING.md,
    textDecorationLine: 'underline',
  },
});

export default SmsInboxScan;
