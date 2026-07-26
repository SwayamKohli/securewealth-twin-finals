// src/screens/TransactionInitiateScreen.tsx
// SecureWealth Twin — Send Money
//
// BACKEND INTEGRATION (was accountsData mock JSON import):
//  • Accounts now come from GET /api/v1/accounts/ on mount.
//  • Backend (snake_case) mapped to the existing account shape so the UI
//    components (AccountSelector, etc.) are unchanged.
//  • Default "From" account = first account returned (no isPrimary field in API).
//  • Payees stay on local mock (payees.json) — no payee endpoint exists.
//  • Screen blocks with a loader until accounts load; shows an error/empty state
//    if the fetch fails or returns nothing.
//  • transactionData now also carries fromAccountId + channel so SecurityReview
//    can call the real transaction/security endpoints. UI/styles unchanged.

import React, { useState, useMemo, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import GlossaryPopup from '../components/common/GlossaryPopup';
import { api, ApiError } from '../api/apiService';
import type { AccountResponse } from '../api/types';

import payeesData from '../../mockData/payees.json';

// ── Types ─────────────────────────────────────────────────────────────────────
type TransferMode = 'self' | 'others' | 'upi';
type PaymentMode = 'IMPS' | 'NEFT' | 'RTGS';

// Local account view-model — same shape the UI expected from the old mock JSON.
interface AccountVM {
  accountId: string;
  bankName: string;
  accountType: string;        // title-case: "Savings" | "Current" | "Salary"
  accountNumberMasked: string;
  balance: number;
}

// ── Mapper: backend → view-model ──────────────────────────────────────────────
const titleCase = (s: string): string =>
  s ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : s;

const mapAccount = (a: AccountResponse): AccountVM => ({
  accountId: a.account_id,
  bankName: a.bank_name,
  accountType: titleCase(String(a.account_type)),
  accountNumberMasked: a.account_number_masked,
  balance: Number(a.balance) || 0,
});

// Map the UI's transfer/payment mode to the API channel enum.
const toChannel = (transferMode: TransferMode, paymentMode: PaymentMode): string => {
  if (transferMode === 'upi') return 'UPI';
  if (transferMode === 'self') return 'IMPS'; // self transfer uses IMPS rails
  return paymentMode; // others → chosen IMPS/NEFT/RTGS
};

// ── Quick amount chips ────────────────────────────────────────────────────────
const QUICK_AMOUNTS = [500, 1000, 5000, 25000, 50000];

// ── Helpers ───────────────────────────────────────────────────────────────────
const formatCurrency = (n: number) => '\u20B9' + n.toLocaleString('en-IN');

// ── Sub-components ────────────────────────────────────────────────────────────

// Transfer mode segmented control
const ModeTabs = ({
  mode,
  onChange,
}: {
  mode: TransferMode;
  onChange: (m: TransferMode) => void;
}) => {
  const tabs: { id: TransferMode; label: string }[] = [
    { id: 'self', label: 'To Self' },
    { id: 'others', label: 'To Others' },
    { id: 'upi', label: 'UPI ID' },
  ];

  return (
    <View style={styles.modeTabsWrap}>
      {tabs.map((tab) => {
        const active = mode === tab.id;
        return (
          <TouchableOpacity
            key={tab.id}
            style={[styles.modeTab, active && styles.modeTabActive]}
            onPress={() => onChange(tab.id)}
            activeOpacity={0.7}
          >
            <Text style={[styles.modeTabText, active && styles.modeTabTextActive]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
};

// Account selector card (From Account)
const AccountSelector = ({
  accounts,
  selectedId,
  onSelect,
  label,
}: {
  accounts: AccountVM[];
  selectedId: string;
  onSelect: (id: string) => void;
  label: string;
}) => {
  const [expanded, setExpanded] = useState(false);
  const selected = accounts.find((a) => a.accountId === selectedId) || accounts[0];

  return (
    <View style={styles.fieldGroup}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TouchableOpacity
        style={styles.accountCard}
        onPress={() => setExpanded(!expanded)}
        activeOpacity={0.7}
      >
        <View style={styles.accountIconWrap}>
          <Feather name="credit-card" size={18} color={COLORS.primary} />
        </View>
        <View style={styles.accountTextWrap}>
          <Text style={styles.accountCardTitle}>
            {selected.bankName} {'\u00B7'} {selected.accountType}
          </Text>
          <Text style={styles.accountCardSub}>{selected.accountNumberMasked}</Text>
        </View>
        <View style={styles.accountBalanceWrap}>
          <Text style={styles.accountCardBalance}>{formatCurrency(selected.balance)}</Text>
          <Feather
            name={expanded ? 'chevron-up' : 'chevron-down'}
            size={16}
            color={COLORS.textTertiary}
          />
        </View>
      </TouchableOpacity>

      {expanded && (
        <View style={styles.accountList}>
          {accounts
            .filter((a) => a.accountId !== selectedId)
            .map((acc) => (
              <TouchableOpacity
                key={acc.accountId}
                style={styles.accountListItem}
                onPress={() => {
                  onSelect(acc.accountId);
                  setExpanded(false);
                }}
                activeOpacity={0.7}
              >
                <View style={styles.accountIconWrap}>
                  <Feather name="credit-card" size={16} color={COLORS.textSecondary} />
                </View>
                <View style={styles.accountTextWrap}>
                  <Text style={styles.accountListTitle}>
                    {acc.bankName} {'\u00B7'} {acc.accountType}
                  </Text>
                  <Text style={styles.accountCardSub}>{acc.accountNumberMasked}</Text>
                </View>
                <Text style={styles.accountListBalance}>{formatCurrency(acc.balance)}</Text>
              </TouchableOpacity>
            ))}
        </View>
      )}
    </View>
  );
};

// Payee avatar chip
const PayeeAvatar = ({
  payee,
  selected,
  onPress,
}: {
  payee: typeof payeesData[0];
  selected: boolean;
  onPress: () => void;
}) => (
  <TouchableOpacity style={styles.payeeChip} onPress={onPress} activeOpacity={0.7}>
    <View
      style={[
        styles.payeeAvatar,
        { backgroundColor: payee.avatarColor + '30' },
        selected && styles.payeeAvatarSelected,
      ]}
    >
      <Text style={[styles.payeeInitials, { color: payee.avatarColor }]}>{payee.initials}</Text>
      {selected && (
        <View style={styles.payeeCheckBadge}>
          <Feather name="check" size={10} color={COLORS.textOnDark} />
        </View>
      )}
    </View>
    <Text style={styles.payeeName} numberOfLines={1}>
      {payee.name.split(' ')[0]}
    </Text>
  </TouchableOpacity>
);

// ── Main Screen ───────────────────────────────────────────────────────────────
const TransactionInitiateScreen = ({ navigation }: any) => {
  const insets = useSafeAreaInsets();

  // ── Accounts (from API) ──
  const [accounts, setAccounts] = useState<AccountVM[]>([]);
  const [loadingAccounts, setLoadingAccounts] = useState(true);
  const [accountsError, setAccountsError] = useState<string | null>(null);

  const [transferMode, setTransferMode] = useState<TransferMode>('others');
  const [fromAccountId, setFromAccountId] = useState<string>('');
  const [selfToAccountId, setSelfToAccountId] = useState<string | null>(null);
  const [selectedPayeeId, setSelectedPayeeId] = useState<string | null>(null);
  const [manualEntry, setManualEntry] = useState('');
  const [amount, setAmount] = useState('');
  const [paymentMode, setPaymentMode] = useState<PaymentMode>('IMPS');
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadAccounts = useCallback(async () => {
    setAccountsError(null);
    setLoadingAccounts(true);
    try {
      const list = await api.getAccounts();
      const mapped = (list || []).map(mapAccount);
      setAccounts(mapped);
      // Default "From" = first account (no isPrimary field in API).
      if (mapped.length > 0) setFromAccountId(mapped[0].accountId);
    } catch (e) {
      const err = e as ApiError;
      setAccountsError(
        err instanceof ApiError && err.isNetworkError
          ? 'Cannot reach the server. Please try again.'
          : 'Could not load your accounts. Please try again.'
      );
    } finally {
      setLoadingAccounts(false);
    }
  }, []);

  useEffect(() => {
    loadAccounts();
  }, [loadAccounts]);

  const fromAccount = accounts.find((a) => a.accountId === fromAccountId);
  const selfAccounts = accounts.filter((a) => a.accountId !== fromAccountId);

  // Reset "to" selection when switching modes
  const handleModeChange = (mode: TransferMode) => {
    setTransferMode(mode);
    setSelfToAccountId(null);
    setSelectedPayeeId(null);
    setManualEntry('');
  };

  const handlePayeeSelect = (payeeId: string) => {
    setSelectedPayeeId((prev) => (prev === payeeId ? null : payeeId));
    setManualEntry('');
  };

  // Build a human-readable "to" summary + whether this is a new recipient
  const toSummary = useMemo(() => {
    if (transferMode === 'self') {
      const acc = selfAccounts.find((a) => a.accountId === selfToAccountId);
      return acc
        ? {
            label: `${acc.bankName} \u00B7 ${acc.accountType}`,
            detail: acc.accountNumberMasked,
            isNew: false,
          }
        : null;
    }

    if (selectedPayeeId) {
      const payee = payeesData.find((p) => p.id === selectedPayeeId)!;
      const detail = transferMode === 'upi' ? payee.upiId : payee.accountNumberMasked;
      return { label: payee.name, detail, isNew: false };
    }

    if (manualEntry.trim().length > 0) {
      return {
        label: transferMode === 'upi' ? 'New UPI recipient' : 'New account',
        detail: manualEntry.trim(),
        isNew: true,
      };
    }

    return null;
  }, [transferMode, selfToAccountId, selectedPayeeId, manualEntry, selfAccounts]);

  const numericAmount = Number(amount) || 0;

  const handleSubmit = () => {
    if (!fromAccount) {
      Alert.alert('No account selected', 'Please choose an account to send from.');
      return;
    }
    // Local const so TypeScript narrows away `undefined` for the rest of this fn.
    const from = fromAccount;
    if (!toSummary) {
      Alert.alert('Add a recipient', 'Please choose or enter who you want to send money to.');
      return;
    }
    if (numericAmount <= 0) {
      Alert.alert('Enter an amount', 'Please enter how much you want to send.');
      return;
    }
    if (numericAmount > from.balance) {
      Alert.alert(
        'Not enough balance',
        `Your ${from.accountType} account has ${formatCurrency(from.balance)} available.`
      );
      return;
    }

    setSubmitting(true);

    const channel = toChannel(transferMode, paymentMode);

    const transactionData = {
      amount: numericAmount,
      // NEW: raw identifiers so SecurityReview can call the real endpoints.
      fromAccountId: from.accountId,
      channel,
      fromAccount: {
        masked: from.accountNumberMasked,
        bankName: from.bankName,
        accountType: from.accountType,
      },
      toLabel: toSummary.label,
      toDetail: toSummary.detail,
      paymentMode:
        transferMode === 'upi' ? 'UPI' : transferMode === 'self' ? 'Self Transfer' : paymentMode,
      note: note.trim(),
      isNewRecipient: toSummary.isNew,
      timestamp: new Date().toISOString(),
    };

    setTimeout(() => {
      setSubmitting(false);
      navigation.navigate('SecurityReview', { transactionData });
    }, 300);
  };

  // ── Loading gate (block until accounts load) ──
  if (loadingAccounts) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.centerText}>Loading your accounts\u2026</Text>
      </View>
    );
  }

  // ── Error / empty gate ──
  if (accountsError || accounts.length === 0) {
    return (
      <View style={styles.centerContainer}>
        <Feather
          name={accountsError ? 'wifi-off' : 'credit-card'}
          size={28}
          color={COLORS.textTertiary}
        />
        <Text style={styles.centerText}>
          {accountsError || 'No accounts available to send from.'}
        </Text>
        {accountsError && (
          <TouchableOpacity style={styles.retryBtn} onPress={loadAccounts} activeOpacity={0.8}>
            <Feather name="refresh-cw" size={16} color={COLORS.textOnDark} />
            <Text style={styles.retryBtnText}>Try Again</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* Trust banner */}
        <View style={styles.trustBanner}>
          <Feather name="shield" size={16} color={COLORS.primary} />
          <Text style={styles.trustBannerText}>
            Every payment is automatically checked to help keep your money safe.
          </Text>
        </View>

        {/* Transfer mode tabs */}
        <ModeTabs mode={transferMode} onChange={handleModeChange} />

        {/* From Account */}
        <AccountSelector
          accounts={accounts}
          selectedId={fromAccountId}
          onSelect={setFromAccountId}
          label="From Account"
        />

        {/* To Account */}
        <View style={styles.fieldGroup}>
          <Text style={styles.fieldLabel}>
            {transferMode === 'self'
              ? 'To Account'
              : transferMode === 'upi'
              ? 'Send To (UPI)'
              : 'Send To'}
          </Text>

          {transferMode === 'self' ? (
            // Self transfer: pick from other own accounts
            <View style={styles.accountList}>
              {selfAccounts.map((acc) => {
                const active = acc.accountId === selfToAccountId;
                return (
                  <TouchableOpacity
                    key={acc.accountId}
                    style={[styles.accountListItem, active && styles.accountListItemActive]}
                    onPress={() => setSelfToAccountId(acc.accountId)}
                    activeOpacity={0.7}
                  >
                    <View style={styles.accountIconWrap}>
                      <Feather
                        name="credit-card"
                        size={16}
                        color={active ? COLORS.primary : COLORS.textSecondary}
                      />
                    </View>
                    <View style={styles.accountTextWrap}>
                      <Text style={styles.accountListTitle}>
                        {acc.bankName} {'\u00B7'} {acc.accountType}
                      </Text>
                      <Text style={styles.accountCardSub}>{acc.accountNumberMasked}</Text>
                    </View>
                    {active && <Feather name="check-circle" size={18} color={COLORS.primary} />}
                  </TouchableOpacity>
                );
              })}
            </View>
          ) : (
            // Others / UPI: recent payees + manual entry
            <>
              <Text style={styles.subtleLabel}>Recent</Text>
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.payeeRow}
              >
                {payeesData.map((payee) => (
                  <PayeeAvatar
                    key={payee.id}
                    payee={payee}
                    selected={selectedPayeeId === payee.id}
                    onPress={() => handlePayeeSelect(payee.id)}
                  />
                ))}
                {/* Add new payee */}
                <TouchableOpacity style={styles.payeeChip} activeOpacity={0.7}>
                  <View style={[styles.payeeAvatar, styles.payeeAvatarAdd]}>
                    <Feather name="plus" size={18} color={COLORS.primary} />
                  </View>
                  <Text style={styles.payeeName}>Add New</Text>
                </TouchableOpacity>
              </ScrollView>

              <View style={styles.orDivider}>
                <View style={styles.orLine} />
                <Text style={styles.orText}>or enter manually</Text>
                <View style={styles.orLine} />
              </View>

              <TextInput
                style={styles.input}
                placeholder={
                  transferMode === 'upi' ? 'Enter UPI ID (e.g. name@bank)' : 'Enter account number'
                }
                placeholderTextColor={COLORS.textTertiary}
                value={selectedPayeeId ? '' : manualEntry}
                onChangeText={(text) => {
                  setManualEntry(text);
                  setSelectedPayeeId(null);
                }}
                autoCapitalize="none"
              />
            </>
          )}
        </View>

        {/* Amount */}
        <View style={styles.fieldGroup}>
          <Text style={styles.fieldLabel}>Amount</Text>
          <View style={styles.amountInputWrap}>
            <Text style={styles.amountCurrency}>{'\u20B9'}</Text>
            <TextInput
              style={styles.amountInput}
              placeholder="0"
              placeholderTextColor={COLORS.textTertiary}
              value={amount}
              onChangeText={(text) => setAmount(text.replace(/[^\d]/g, ''))}
              keyboardType="number-pad"
              maxLength={9}
            />
          </View>

          {/* Quick amount chips */}
          <View style={styles.chipsRow}>
            {QUICK_AMOUNTS.map((amt) => (
              <TouchableOpacity
                key={amt}
                style={[styles.amountChip, numericAmount === amt && styles.amountChipActive]}
                onPress={() => setAmount(String(amt))}
                activeOpacity={0.7}
              >
                <Text
                  style={[
                    styles.amountChipText,
                    numericAmount === amt && styles.amountChipTextActive,
                  ]}
                >
                  {'\u20B9'}{amt >= 1000 ? `${amt / 1000}k` : amt}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Balance hint */}
          <Text style={styles.balanceHint}>Available: {formatCurrency(fromAccount?.balance ?? 0)}</Text>
        </View>

        {/* Payment Mode (hidden for UPI) */}
        {transferMode !== 'upi' && (
          <View style={styles.fieldGroup}>
            <Text style={styles.fieldLabel}>Payment Mode</Text>
            <View style={styles.paymentModeRow}>
              {(['IMPS', 'NEFT', 'RTGS'] as PaymentMode[]).map((mode) => {
                const active = paymentMode === mode;
                return (
                  <TouchableOpacity
                    key={mode}
                    style={[styles.paymentModeCard, active && styles.paymentModeCardActive]}
                    onPress={() => setPaymentMode(mode)}
                    activeOpacity={0.7}
                  >
                    <View style={styles.paymentModeHeader}>
                      <Text
                        style={[styles.paymentModeName, active && styles.paymentModeNameActive]}
                      >
                        {mode}
                      </Text>
                      <GlossaryPopup term={mode as any}>
                        <Feather name="help-circle" size={14} color={COLORS.textTertiary} />
                      </GlossaryPopup>
                    </View>
                    <Text style={styles.paymentModeDesc}>
                      {mode === 'IMPS' && 'Within minutes'}
                      {mode === 'NEFT' && 'A few hours'}
                      {mode === 'RTGS' && 'Large amounts'}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>
        )}

        {/* Note */}
        <View style={styles.fieldGroup}>
          <Text style={styles.fieldLabel}>Note (optional)</Text>
          <TextInput
            style={[styles.input, styles.noteInput]}
            placeholder="What's this for?"
            placeholderTextColor={COLORS.textTertiary}
            value={note}
            onChangeText={setNote}
            multiline
          />
        </View>

        {/* Bottom spacing so sticky button doesn't overlap last field */}
        <View style={{ height: 100 }} />
      </ScrollView>

      {/* Sticky footer button */}
      <View style={[styles.footer, { paddingBottom: Math.max(insets.bottom, SPACING.md) }]}>
        <TouchableOpacity
          style={[styles.submitBtn, (!toSummary || numericAmount <= 0) && styles.submitBtnDisabled]}
          onPress={handleSubmit}
          disabled={submitting || !toSummary || numericAmount <= 0}
          activeOpacity={0.8}
        >
          <Text style={styles.submitBtnText}>
            {submitting
              ? 'Reviewing\u2026'
              : numericAmount > 0
              ? `Review & Pay ${formatCurrency(numericAmount)}`
              : 'Review & Pay'}
          </Text>
          <Feather name="arrow-right" size={18} color={COLORS.textOnDark} />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
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

  // Loading / error / empty gate
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
    padding: SPACING.xl,
    gap: SPACING.md,
  },
  centerText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    textAlign: 'center',
  },
  retryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.lg,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.lg,
    marginTop: SPACING.sm,
  },
  retryBtnText: {
    ...TYPOGRAPHY.buttonSm,
    color: COLORS.textOnDark,
  },

  trustBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    backgroundColor: COLORS.primaryVeryLight,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
  },
  trustBannerText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.primaryMedium,
    flex: 1,
    lineHeight: 18,
  },

  modeTabsWrap: {
    flexDirection: 'row',
    backgroundColor: COLORS.surfaceLight,
    borderRadius: BORDER_RADIUS.full,
    padding: 4,
    marginBottom: SPACING.lg,
  },
  modeTab: {
    flex: 1,
    paddingVertical: SPACING.sm,
    borderRadius: BORDER_RADIUS.full,
    alignItems: 'center',
  },
  modeTabActive: {
    backgroundColor: COLORS.primary,
    ...SHADOWS.small,
  },
  modeTabText: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.textSecondary,
  },
  modeTabTextActive: {
    color: COLORS.textOnDark,
  },

  fieldGroup: {
    marginBottom: SPACING.lg,
  },
  fieldLabel: {
    ...TYPOGRAPHY.label,
    color: COLORS.textSecondary,
    marginBottom: SPACING.sm,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  subtleLabel: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    marginBottom: SPACING.sm,
  },

  accountCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    gap: SPACING.md,
    ...SHADOWS.small,
  },
  accountIconWrap: {
    width: 36,
    height: 36,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.primaryVeryLight,
    justifyContent: 'center',
    alignItems: 'center',
    flexShrink: 0,
  },
  accountTextWrap: {
    flex: 1,
    minWidth: 0,
  },
  accountCardTitle: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.text,
    fontWeight: '600',
  },
  accountCardSub: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    marginTop: 1,
  },
  accountBalanceWrap: {
    alignItems: 'flex-end',
    gap: 2,
    flexShrink: 0,
  },
  accountCardBalance: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.text,
    fontWeight: '700',
  },
  accountList: {
    marginTop: SPACING.sm,
    gap: SPACING.sm,
  },
  accountListItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    gap: SPACING.md,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  accountListItemActive: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primaryVeryLight,
  },
  accountListTitle: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.text,
    fontWeight: '600',
  },
  accountListBalance: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },

  payeeRow: {
    gap: SPACING.md,
    paddingBottom: SPACING.xs,
  },
  payeeChip: {
    alignItems: 'center',
    width: 64,
  },
  payeeAvatar: {
    width: 52,
    height: 52,
    borderRadius: BORDER_RADIUS.full,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.xs,
    position: 'relative',
  },
  payeeAvatarSelected: {
    borderWidth: 2,
    borderColor: COLORS.primary,
  },
  payeeAvatarAdd: {
    backgroundColor: COLORS.primaryVeryLight,
    borderWidth: 1.5,
    borderColor: COLORS.primary,
    borderStyle: 'dashed',
  },
  payeeInitials: {
    ...TYPOGRAPHY.bodyMedium,
    fontWeight: '700',
  },
  payeeCheckBadge: {
    position: 'absolute',
    bottom: -2,
    right: -2,
    width: 16,
    height: 16,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: COLORS.background,
  },
  payeeName: {
    ...TYPOGRAPHY.caption,
    color: COLORS.text,
    textAlign: 'center',
  },

  orDivider: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginVertical: SPACING.md,
  },
  orLine: {
    flex: 1,
    height: 1,
    backgroundColor: COLORS.border,
  },
  orText: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
  },

  input: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.lg,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.md,
    ...TYPOGRAPHY.body,
    color: COLORS.text,
  },
  noteInput: {
    minHeight: 60,
    textAlignVertical: 'top',
  },

  amountInputWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.lg,
    paddingHorizontal: SPACING.lg,
  },
  amountCurrency: {
    ...TYPOGRAPHY.h2,
    color: COLORS.textTertiary,
    marginRight: SPACING.sm,
  },
  amountInput: {
    flex: 1,
    ...TYPOGRAPHY.display,
    color: COLORS.text,
    paddingVertical: SPACING.md,
  },
  chipsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
    marginTop: SPACING.md,
  },
  amountChip: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.surfaceLight,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  amountChipActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  amountChipText: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.textSecondary,
  },
  amountChipTextActive: {
    color: COLORS.textOnDark,
  },
  balanceHint: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    marginTop: SPACING.sm,
  },

  paymentModeRow: {
    flexDirection: 'row',
    gap: SPACING.sm,
  },
  paymentModeCard: {
    flex: 1,
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    borderWidth: 1.5,
    borderColor: COLORS.border,
  },
  paymentModeCardActive: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primaryVeryLight,
  },
  paymentModeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  paymentModeName: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.textSecondary,
    fontWeight: '700',
  },
  paymentModeNameActive: {
    color: COLORS.primary,
  },
  paymentModeDesc: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    marginTop: 2,
  },

  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    padding: SPACING.lg,
    ...SHADOWS.large,
  },
  submitBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.lg,
    paddingVertical: SPACING.md,
    gap: SPACING.sm,
  },
  submitBtnDisabled: {
    backgroundColor: COLORS.borderDark,
  },
  submitBtnText: {
    ...TYPOGRAPHY.button,
    color: COLORS.textOnDark,
  },
});

export default TransactionInitiateScreen;