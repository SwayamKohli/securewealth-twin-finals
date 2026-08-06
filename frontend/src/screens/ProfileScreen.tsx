// src/screens/ProfileScreen.tsx
// ─────────────────────────────────────────────────────────────────────────────
// SecureWealth Twin — My Profile
//
// Replaces the placeholder. Everything here is live:
//   • Identity        GET /auth/session  +  GET /users/me
//   • Trusted devices GET /devices        (task 4.4 — now visible to the customer)
//   • Consent         GET/POST/DELETE /aggregation/consent  (task 2.1)
//   • Language        EN / हिन्दी / ਪੰਜਾਬੀ  (task 1.5)
//   • Sign out        POST /auth/logout, then local token clear
// ─────────────────────────────────────────────────────────────────────────────

import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Alert,
  Switch,
} from 'react-native';
import { Feather } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import { api } from '../api/apiService';
import { describeTrust, getStoredDeviceId } from '../api/deviceSession';
import { useI18n, LANGUAGES } from '../i18n';
import { ProfileSkeleton } from '../components/common/Skeleton';
import type { DeviceResponse, SessionResponse } from '../api/types';

const Section = ({
  title, icon, children, action,
}: {
  title: string; icon: string; children: React.ReactNode; action?: React.ReactNode;
}) => (
  <View style={styles.section}>
    <View style={styles.sectionHead}>
      <Feather name={icon as any} size={14} color={COLORS.primary} />
      <Text style={styles.sectionTitle}>{title}</Text>
      {action}
    </View>
    <View style={styles.card}>{children}</View>
  </View>
);

const ProfileScreen = ({ handleLogout }: { handleLogout?: () => void }) => {
  const { t, language, setLanguage } = useI18n();

  const [session, setSession] = useState<SessionResponse | null>(null);
  const [devices, setDevices] = useState<DeviceResponse[]>([]);
  const [consent, setConsent] = useState<boolean | null>(null);
  const [thisDeviceId, setThisDeviceId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [busy, setBusy] = useState(false);
  // Task 4.4 — the Device Trust explainer existed on the backend but nothing
  // ever called it. It turns the raw status into a sentence the customer can
  // act on, so it belongs exactly here, next to the device list.
  const [trustMessage, setTrustMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [s, d, c, local] = await Promise.allSettled([
      api.getSession(),
      api.getDevices(),
      api.getConsent(),
      getStoredDeviceId(),
    ]);
    if (s.status === 'fulfilled') setSession(s.value);
    if (d.status === 'fulfilled') setDevices(d.value || []);
    if (c.status === 'fulfilled') setConsent(c.value.aa_consent);
    if (local.status === 'fulfilled') setThisDeviceId(local.value);

    // Explain the device the customer is holding right now.
    if (d.status === 'fulfilled' && d.value?.length) {
      const localId = local.status === 'fulfilled' ? local.value : null;
      const current = d.value.find((x) => x.device_id === localId) || d.value[0];
      api
        .explainDeviceTrust({
          trust_result: {
            device_status: current.trust_status,
            confidence: (current as Record<string, any>).trust_confidence ?? 0,
            age_days: (current as Record<string, any>).device_age_days ?? 0,
            signals: [],
          },
          user_profile: {
            full_name: s.status === 'fulfilled' ? s.value.full_name : '',
          },
          language,
        })
        .then((res) => setTrustMessage(res?.customer_message || null))
        .catch(() => setTrustMessage(null));
    }
    setLoading(false);
    setRefreshing(false);
    // The device-trust message is generated per language, so switching it must
    // refetch rather than leave the previous language's sentence on screen.
  }, [language]);

  useEffect(() => {
    load();
  }, [load]);

  const toggleConsent = async (next: boolean) => {
    setBusy(true);
    try {
      const res = next ? await api.grantConsent() : await api.revokeConsent();
      setConsent(res.aa_consent);
      if (!next) {
        Alert.alert(
          'Consent withdrawn',
          'Your accounts are no longer combined into one view. You can turn this '
            + 'back on any time.'
        );
      }
    } catch {
      Alert.alert('Could not update consent', 'Please try again in a moment.');
    } finally {
      setBusy(false);
    }
  };

  const signOut = () => {
    Alert.alert(t('profile.signOut'), t('profile.signOutConfirm'), [
      { text: t('common.cancel'), style: 'cancel' },
      {
        text: t('profile.signOut'),
        style: 'destructive',
        onPress: async () => {
          // Tell the server, then clear locally. api.logout() always clears the
          // local token even if the server call fails.
          await api.logout();
          handleLogout?.();
        },
      },
    ]);
  };

  if (loading) return <ProfileSkeleton />;

  const initials = (session?.full_name || 'SW')
    .split(' ')
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => {
            setRefreshing(true);
            load();
          }}
          tintColor={COLORS.primary}
        />
      }
    >
      {/* ── Identity ── */}
      <View style={styles.hero}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{initials}</Text>
        </View>
        <Text style={styles.name}>{session?.full_name || 'Customer'}</Text>
        {session?.customer_id ? (
          <View style={styles.idPill}>
            <Feather name="credit-card" size={12} color={COLORS.primaryDark} />
            <Text style={styles.idPillText}>{session.customer_id}</Text>
          </View>
        ) : null}
      </View>

      <Section title={t('profile.accountDetails')} icon="user">
        <Row label={t('profile.mobile')} value={session?.phone || '—'} />
        <Row label={t('profile.email')} value={session?.email || '—'} />
        <Row
          label={t('profile.lastLogin')}
          value={
            session?.last_login
              ? new Date(session.last_login).toLocaleString('en-IN', { hour12: true })
              : 'This is your first session'
          }
          last
        />
      </Section>

      {/* ── Trusted devices (task 4.4) ── */}
      <Section title={t('profile.devices')} icon="smartphone">
        {devices.length === 0 ? (
          <Text style={styles.empty}>{t('profile.noDevices')}</Text>
        ) : (
          devices.map((d, i) => {
            const trust = describeTrust(d.trust_status);
            const isThis = d.device_id === thisDeviceId;
            const trusted = String(d.trust_status).toUpperCase() === 'TRUSTED';
            return (
              <View
                key={d.device_id}
                style={[styles.deviceRow, i === devices.length - 1 && styles.rowLast]}
              >
                <View
                  style={[
                    styles.deviceIcon,
                    { backgroundColor: trusted ? '#DCFCE7' : '#FEF3C7' },
                  ]}
                >
                  <Feather
                    name={trusted ? 'shield' : 'shield-off'}
                    size={16}
                    color={trusted ? '#16A34A' : '#B45309'}
                  />
                </View>
                <View style={styles.flex1}>
                  <View style={styles.deviceTitleRow}>
                    <Text style={styles.deviceName}>{d.device_name}</Text>
                    {isThis && (
                      <View style={styles.thisPill}>
                        <Text style={styles.thisPillText}>{t('profile.thisDevice')}</Text>
                      </View>
                    )}
                  </View>
                  <Text style={styles.deviceTrust}>{trust.label}</Text>
                  <Text style={styles.deviceDetail}>{trust.detail}</Text>
                </View>
              </View>
            );
          })
        )}
        {trustMessage ? (
          <View style={styles.trustExplain}>
            <Feather name="message-circle" size={13} color={COLORS.primaryDark} />
            <Text style={styles.trustExplainText}>{trustMessage}</Text>
          </View>
        ) : null}

        <Text style={styles.sectionNote}>{t('profile.devicesNote')}</Text>
      </Section>

      {/* ── Consent (task 2.1) ── */}
      <Section title={t('profile.aggregation')} icon="link-2">
        <View style={styles.switchRow}>
          <View style={styles.flex1}>
            <Text style={styles.switchLabel}>{t('profile.combineLabel')}</Text>
            <Text style={styles.switchHint}>{t('profile.combineHint')}</Text>
          </View>
          {busy ? (
            <ActivityIndicator color={COLORS.primary} />
          ) : (
            <Switch
              value={!!consent}
              onValueChange={toggleConsent}
              trackColor={{ false: COLORS.border, true: COLORS.primaryLight }}
              thumbColor={consent ? COLORS.primary : '#f4f3f4'}
            />
          )}
        </View>
      </Section>

      {/* ── Language (task 1.5) ── */}
      <Section title={t('common.language')} icon="globe">
        <View style={styles.langRow}>
          {LANGUAGES.map((l) => (
            <TouchableOpacity
              key={l.code}
              style={[styles.langBtn, language === l.code && styles.langBtnOn]}
              onPress={() => setLanguage(l.code)}
              activeOpacity={0.8}
            >
              <Text style={[styles.langText, language === l.code && styles.langTextOn]}>
                {l.native}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </Section>

      <TouchableOpacity style={styles.signOut} onPress={signOut} activeOpacity={0.8}>
        <Feather name="log-out" size={16} color={COLORS.danger} />
        <Text style={styles.signOutText}>{t('profile.signOut')}</Text>
      </TouchableOpacity>

      <Text style={styles.version}>SecureWealth Twin · Wealth First. Security Always.</Text>
    </ScrollView>
  );
};

const Row = ({ label, value, last }: { label: string; value: string; last?: boolean }) => (
  <View style={[styles.row, last && styles.rowLast]}>
    <Text style={styles.rowLabel}>{label}</Text>
    <Text style={styles.rowValue} numberOfLines={1}>
      {value}
    </Text>
  </View>
);

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: SPACING.lg, paddingBottom: SPACING.xxl },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.background },
  flex1: { flex: 1 },

  hero: { alignItems: 'center', marginBottom: SPACING.xl },
  avatar: {
    width: 72, height: 72, borderRadius: 36, backgroundColor: COLORS.primary,
    alignItems: 'center', justifyContent: 'center', ...SHADOWS.medium,
  },
  avatarText: { ...TYPOGRAPHY.h1, color: COLORS.textOnDark },
  name: { ...TYPOGRAPHY.h2, color: COLORS.text, marginTop: SPACING.md },
  idPill: {
    flexDirection: 'row', alignItems: 'center', gap: SPACING.xs,
    backgroundColor: COLORS.primaryVeryLight, borderRadius: 999,
    paddingHorizontal: SPACING.md, paddingVertical: 5, marginTop: SPACING.xs,
  },
  idPillText: {
    ...TYPOGRAPHY.caption, color: COLORS.primaryDark,
    fontWeight: '700', letterSpacing: 1,
  },

  section: { marginBottom: SPACING.lg },
  sectionHead: {
    flexDirection: 'row', alignItems: 'center', gap: SPACING.xs, marginBottom: SPACING.sm,
  },
  sectionTitle: {
    ...TYPOGRAPHY.captionBold, color: COLORS.textSecondary,
    textTransform: 'uppercase', letterSpacing: 0.7, flex: 1,
  },
  card: {
    backgroundColor: COLORS.surface, borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1, borderColor: COLORS.border, padding: SPACING.md,
  },
  sectionNote: {
    ...TYPOGRAPHY.caption, color: COLORS.textTertiary,
    marginTop: SPACING.sm, lineHeight: 16,
  },

  row: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingVertical: SPACING.sm, borderBottomWidth: 1, borderBottomColor: COLORS.divider,
    gap: SPACING.md,
  },
  rowLast: { borderBottomWidth: 0 },
  rowLabel: { ...TYPOGRAPHY.body, color: COLORS.textSecondary },
  rowValue: { ...TYPOGRAPHY.bodyMedium, color: COLORS.text, flexShrink: 1, textAlign: 'right' },

  deviceRow: {
    flexDirection: 'row', gap: SPACING.md, paddingVertical: SPACING.sm,
    borderBottomWidth: 1, borderBottomColor: COLORS.divider,
  },
  deviceIcon: {
    width: 36, height: 36, borderRadius: 10,
    alignItems: 'center', justifyContent: 'center',
  },
  deviceTitleRow: { flexDirection: 'row', alignItems: 'center', gap: SPACING.xs },
  deviceName: { ...TYPOGRAPHY.bodyMedium, color: COLORS.text },
  thisPill: {
    backgroundColor: COLORS.primaryVeryLight, borderRadius: 999,
    paddingHorizontal: SPACING.sm, paddingVertical: 2,
  },
  thisPillText: { fontSize: 8.5, fontWeight: '800', color: COLORS.primaryDark, letterSpacing: 0.5 },
  deviceTrust: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary, fontWeight: '700', marginTop: 1 },
  deviceDetail: { ...TYPOGRAPHY.caption, color: COLORS.textTertiary, marginTop: 1, lineHeight: 15 },

  trustExplain: {
    flexDirection: 'row',
    gap: SPACING.sm,
    backgroundColor: COLORS.primaryVeryLight,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginTop: SPACING.sm,
  },
  trustExplainText: { ...TYPOGRAPHY.caption, color: COLORS.primaryDark, flex: 1, lineHeight: 17 },

  switchRow: { flexDirection: 'row', alignItems: 'center', gap: SPACING.md },
  switchLabel: { ...TYPOGRAPHY.bodyMedium, color: COLORS.text },
  switchHint: { ...TYPOGRAPHY.caption, color: COLORS.textTertiary, marginTop: 2, lineHeight: 16 },

  langRow: { flexDirection: 'row', gap: SPACING.sm },
  langBtn: {
    flex: 1, alignItems: 'center', paddingVertical: SPACING.sm,
    borderRadius: BORDER_RADIUS.md, borderWidth: 1.5, borderColor: COLORS.border,
  },
  langBtnOn: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  langText: { ...TYPOGRAPHY.body, color: COLORS.textSecondary, fontWeight: '600' },
  langTextOn: { color: COLORS.textOnDark },

  empty: { ...TYPOGRAPHY.body, color: COLORS.textTertiary, textAlign: 'center', paddingVertical: SPACING.md },

  signOut: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: SPACING.sm,
    backgroundColor: COLORS.surface, borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1.5, borderColor: COLORS.danger, paddingVertical: SPACING.md,
    marginTop: SPACING.sm,
  },
  signOutText: { ...TYPOGRAPHY.bodyMedium, color: COLORS.danger },

  version: {
    ...TYPOGRAPHY.caption, color: COLORS.textTertiary,
    textAlign: 'center', marginTop: SPACING.lg,
  },
});

export default ProfileScreen;
