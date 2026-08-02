// src/components/LinkedBanksCard.tsx
// ─────────────────────────────────────────────────────────────────────────────
// Account Aggregation status, surfaced on the Wealth tab (task 2.1).
//
// Shows how many external accounts feed the net-worth figure, when they were
// last refreshed, and lets the customer re-sync or link another bank. Without
// this the aggregation layer was invisible: the number was aggregated, but
// nothing told the customer where it came from.
//
// Endpoints: GET /aggregation/status, POST /aggregation/sync,
//            POST /aggregation/accounts/link
// ─────────────────────────────────────────────────────────────────────────────

import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Modal,
  TextInput,
  ScrollView,
  Alert,
} from 'react-native';
import { Feather } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS } from '../constants/theme';
import { api } from '../api/apiService';
import { useI18n } from '../i18n';
import type { AggregationStatusResponse } from '../api/types';

const ACCOUNT_TYPES = ['SAVINGS', 'CURRENT', 'SALARY'] as const;

function relativeTime(iso: string | null): string {
  if (!iso) return 'Not synced yet';
  const then = new Date(iso).getTime();
  const mins = Math.floor((Date.now() - then) / 60000);
  if (mins < 1) return 'Synced just now';
  if (mins < 60) return `Synced ${mins} min ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `Synced ${hrs} hr${hrs > 1 ? 's' : ''} ago`;
  const days = Math.floor(hrs / 24);
  return `Synced ${days} day${days > 1 ? 's' : ''} ago`;
}

type Props = {
  /** Called after a sync or a new link so the parent can refresh totals. */
  onChanged?: () => void;
};

const LinkedBanksCard = ({ onChanged }: Props) => {
  const { t } = useI18n();
  const [status, setStatus] = useState<AggregationStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [showLink, setShowLink] = useState(false);

  const [bankName, setBankName] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [accountType, setAccountType] = useState<string>('SAVINGS');
  const [balance, setBalance] = useState('');
  const [linking, setLinking] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const loadStatus = useCallback(async () => {
    try {
      setStatus(await api.getAggregationStatus());
    } catch {
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const sync = async () => {
    setSyncing(true);
    try {
      const res = await api.syncAggregation();
      await loadStatus();
      onChanged?.();
      Alert.alert(
        'Accounts refreshed',
        res.message || `${res.synced_accounts} account(s) refreshed.`
      );
    } catch {
      Alert.alert('Sync failed', 'We could not refresh your linked accounts. Please try again.');
    } finally {
      setSyncing(false);
    }
  };

  const submitLink = async () => {
    setFormError(null);
    if (bankName.trim().length < 2) return setFormError('Enter the bank name.');
    if (accountNumber.trim().length < 4) return setFormError('Account number must be at least 4 characters.');
    const bal = Number(balance);
    if (!balance || Number.isNaN(bal) || bal < 0) return setFormError('Enter a valid balance.');

    setLinking(true);
    try {
      await api.linkAccount({
        bank_name: bankName.trim(),
        account_type: accountType,
        account_number: accountNumber.trim(),
        balance: bal,
        currency: 'INR',
      });
      setShowLink(false);
      setBankName('');
      setAccountNumber('');
      setBalance('');
      await loadStatus();
      onChanged?.();
    } catch {
      setFormError('We could not link this account. Please check the details and try again.');
    } finally {
      setLinking(false);
    }
  };

  const healthy = status?.healthy ?? false;
  const count = status?.accounts_connected ?? 0;

  return (
    <View style={styles.card}>
      <View style={styles.head}>
        <View style={styles.headIcon}>
          <Feather name="link-2" size={15} color={COLORS.primary} />
        </View>
        <View style={styles.flex1}>
          <Text style={styles.title}>{t('wealth.linkedAccounts')}</Text>
          {loading ? (
            <Text style={styles.sub}>Checking…</Text>
          ) : (
            <Text style={styles.sub}>
              {count === 0
                ? t('wealth.noBanksLinked')
                : `${count} account${count > 1 ? 's' : ''} feeding your net worth`}
            </Text>
          )}
        </View>
        {!loading && (
          <View style={[styles.pill, { backgroundColor: healthy ? '#DCFCE7' : '#FEF3C7' }]}>
            <Text style={[styles.pillText, { color: healthy ? '#15803D' : '#B45309' }]}>
              {status?.status || (healthy ? 'HEALTHY' : 'UNKNOWN')}
            </Text>
          </View>
        )}
      </View>

      {!loading && <Text style={styles.synced}>{relativeTime(status?.last_synced ?? null)}</Text>}

      <View style={styles.actions}>
        <TouchableOpacity
          style={styles.secondaryBtn}
          onPress={sync}
          disabled={syncing}
          activeOpacity={0.8}
        >
          {syncing ? (
            <ActivityIndicator size="small" color={COLORS.primary} />
          ) : (
            <>
              <Feather name="refresh-cw" size={13} color={COLORS.primary} />
              <Text style={styles.secondaryBtnText}>{t('common.refresh')}</Text>
            </>
          )}
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.secondaryBtn}
          onPress={() => setShowLink(true)}
          activeOpacity={0.8}
        >
          <Feather name="plus" size={13} color={COLORS.primary} />
          <Text style={styles.secondaryBtnText}>{t('wealth.linkBank')}</Text>
        </TouchableOpacity>
      </View>

      {/* ── Link a bank ── */}
      <Modal visible={showLink} transparent animationType="slide" onRequestClose={() => setShowLink(false)}>
        <View style={styles.modalRoot}>
          <View style={styles.sheet}>
            <View style={styles.sheetHead}>
              <Text style={styles.sheetTitle}>{t('wealth.linkAnother')}</Text>
              <TouchableOpacity
                onPress={() => setShowLink(false)}
                hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
                accessibilityRole="button"
                accessibilityLabel={t('a11y.close')}
              >
                <Feather name="x" size={20} color={COLORS.textSecondary} />
              </TouchableOpacity>
            </View>
            <ScrollView keyboardShouldPersistTaps="handled">
              <Text style={styles.label}>{t('wealth.bankName')}</Text>
              <TextInput
                style={styles.input}
                value={bankName}
                onChangeText={setBankName}
                placeholder="e.g. State Bank of India"
                placeholderTextColor={COLORS.textTertiary}
              />

              <Text style={styles.label}>{t('wealth.accountType')}</Text>
              <View style={styles.typeRow}>
                {ACCOUNT_TYPES.map((type) => (
                  <TouchableOpacity
                    key={type}
                    style={[styles.typeBtn, accountType === type && styles.typeBtnOn]}
                    onPress={() => setAccountType(type)}
                    activeOpacity={0.8}
                  >
                    <Text
                      style={[styles.typeText, accountType === type && styles.typeTextOn]}
                    >
                      {type.charAt(0) + type.slice(1).toLowerCase()}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={styles.label}>{t('wealth.accountNumber')}</Text>
              <TextInput
                style={styles.input}
                value={accountNumber}
                onChangeText={setAccountNumber}
                placeholder="Account number"
                placeholderTextColor={COLORS.textTertiary}
                keyboardType="number-pad"
              />

              <Text style={styles.label}>Current balance (₹)</Text>
              <TextInput
                style={styles.input}
                value={balance}
                onChangeText={setBalance}
                placeholder="0"
                placeholderTextColor={COLORS.textTertiary}
                keyboardType="decimal-pad"
              />

              {formError ? <Text style={styles.formError}>{formError}</Text> : null}

              <TouchableOpacity
                style={[styles.primaryBtn, linking && { opacity: 0.6 }]}
                onPress={submitLink}
                disabled={linking}
                activeOpacity={0.85}
              >
                {linking ? (
                  <ActivityIndicator color={COLORS.textOnDark} />
                ) : (
                  <Text style={styles.primaryBtnText}>{t('wealth.linkAccountBtn')}</Text>
                )}
              </TouchableOpacity>

              <Text style={styles.sheetNote}>
                Read-only. Linking adds this account to your net worth and advice —
                it does not let us move money.
              </Text>
            </ScrollView>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: COLORS.surface, borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1, borderColor: COLORS.border,
    padding: SPACING.md, marginBottom: SPACING.lg,
  },
  flex1: { flex: 1 },
  head: { flexDirection: 'row', alignItems: 'center', gap: SPACING.sm },
  headIcon: {
    width: 32, height: 32, borderRadius: 9,
    backgroundColor: COLORS.primaryVeryLight,
    alignItems: 'center', justifyContent: 'center',
  },
  title: { ...TYPOGRAPHY.bodyMedium, color: COLORS.text },
  sub: { ...TYPOGRAPHY.caption, color: COLORS.textTertiary, marginTop: 1 },
  pill: { borderRadius: 999, paddingHorizontal: SPACING.sm, paddingVertical: 3 },
  pillText: { fontSize: 9, fontWeight: '800', letterSpacing: 0.5 },
  synced: { ...TYPOGRAPHY.caption, color: COLORS.textTertiary, marginTop: SPACING.sm },

  actions: { flexDirection: 'row', gap: SPACING.sm, marginTop: SPACING.md },
  secondaryBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 6, borderWidth: 1.5, borderColor: COLORS.primaryLight,
    borderRadius: BORDER_RADIUS.md, paddingVertical: SPACING.sm,
  },
  secondaryBtnText: { ...TYPOGRAPHY.caption, color: COLORS.primary, fontWeight: '700' },

  modalRoot: { flex: 1, backgroundColor: 'rgba(0,0,0,0.45)', justifyContent: 'flex-end' },
  sheet: {
    backgroundColor: COLORS.surface,
    borderTopLeftRadius: BORDER_RADIUS.xl, borderTopRightRadius: BORDER_RADIUS.xl,
    padding: SPACING.lg, maxHeight: '85%',
  },
  sheetHead: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between', marginBottom: SPACING.md,
  },
  sheetTitle: { ...TYPOGRAPHY.h3, color: COLORS.text },
  label: {
    ...TYPOGRAPHY.captionBold, color: COLORS.textSecondary,
    marginTop: SPACING.md, marginBottom: SPACING.xs,
  },
  input: {
    borderWidth: 1.5, borderColor: COLORS.border, borderRadius: BORDER_RADIUS.md,
    paddingHorizontal: SPACING.md, paddingVertical: SPACING.sm,
    ...TYPOGRAPHY.body, color: COLORS.text, backgroundColor: COLORS.background,
  },
  typeRow: { flexDirection: 'row', gap: SPACING.sm },
  typeBtn: {
    flex: 1, alignItems: 'center', paddingVertical: SPACING.sm,
    borderRadius: BORDER_RADIUS.md, borderWidth: 1.5, borderColor: COLORS.border,
  },
  typeBtnOn: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  typeText: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary, fontWeight: '600' },
  typeTextOn: { color: COLORS.textOnDark },
  formError: { ...TYPOGRAPHY.caption, color: COLORS.danger, marginTop: SPACING.sm },
  primaryBtn: {
    backgroundColor: COLORS.primary, borderRadius: BORDER_RADIUS.lg,
    paddingVertical: SPACING.md, alignItems: 'center', marginTop: SPACING.lg,
  },
  primaryBtnText: { ...TYPOGRAPHY.bodyMedium, color: COLORS.textOnDark, fontWeight: '700' },
  sheetNote: {
    ...TYPOGRAPHY.caption, color: COLORS.textTertiary,
    textAlign: 'center', marginTop: SPACING.md, marginBottom: SPACING.lg, lineHeight: 16,
  },
});

export default LinkedBanksCard;
