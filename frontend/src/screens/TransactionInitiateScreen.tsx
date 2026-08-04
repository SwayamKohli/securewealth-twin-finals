// src/screens/TransactionInitiateScreen.tsx
// SecureWealth Twin — INVEST (task 1.2 / 2.3: investment-only workflow)
//
// Savings → Mutual Fund. Person-to-person and merchant transfers are gone.
// The customer picks a fund, an amount, and a source Savings account;
// SecurityReview then runs the real-time fraud check and completes the
// investment. transactionData keeps the same contract keys SecurityReview
// already consumes (amount, fromAccountId, channel, toLabel, toDetail, …).

import React, { useState, useEffect, useCallback } from 'react';
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

import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import { api, ApiError } from '../api/apiService';
import { useI18n } from '../i18n';
import type { AccountResponse } from '../api/types';

// ── Types ─────────────────────────────────────────────────────────────────────
interface AccountVM {
  accountId: string;
  bankName: string;
  accountType: string;
  accountNumberMasked: string;
  balance: number;
}

interface FundVM {
  id: string;
  name: string;
  category: string;       // backend fund_category value
  categoryLabel: string;  // display label
  risk: 'Low' | 'Moderate' | 'High';
  blurb: string;
  color: string;
  icon: string;
}

// ── Curated mutual-fund categories (behavioural products only — no stocks) ────
const FUNDS: FundVM[] = [
  {
    id: 'f1',
    name: 'Bluechip Equity Fund SIP',
    category: 'EQUITY_MUTUAL_FUND',
    categoryLabel: 'Equity Mutual Fund',
    risk: 'High',
    blurb: 'Long-term growth from large, established companies.',
    color: '#6366F1',
    icon: 'trending-up',
  },
  {
    id: 'f2',
    name: 'Nifty 50 Index Fund SIP',
    category: 'INDEX_MUTUAL_FUND',
    categoryLabel: 'Index Mutual Fund',
    risk: 'Moderate',
    blurb: 'Low-cost fund that simply tracks the market.',
    color: '#0EA5E9',
    icon: 'bar-chart-2',
  },
  {
    id: 'f3',
    name: 'Balanced Advantage Fund SIP',
    category: 'BALANCED_MUTUAL_FUND',
    categoryLabel: 'Balanced Mutual Fund',
    risk: 'Moderate',
    blurb: 'A mix of equity and debt for steadier growth.',
    color: '#8B5CF6',
    icon: 'shuffle',
  },
  {
    id: 'f4',
    name: 'Corporate Bond Debt Fund SIP',
    category: 'DEBT_MUTUAL_FUND',
    categoryLabel: 'Debt Mutual Fund',
    risk: 'Low',
    blurb: 'Stable returns from high-quality bonds.',
    color: '#10B981',
    icon: 'shield',
  },
  {
    id: 'f5',
    name: 'ELSS Tax Saver Fund SIP',
    category: 'ELSS_MUTUAL_FUND',
    categoryLabel: 'ELSS (Tax Saving)',
    risk: 'High',
    blurb: 'Save tax under 80C with a 3-year lock-in.',
    color: '#F59E0B',
    icon: 'percent',
  },
  {
    id: 'f6',
    name: 'Liquid Fund',
    category: 'LIQUID_MUTUAL_FUND',
    categoryLabel: 'Liquid Mutual Fund',
    risk: 'Low',
    blurb: 'Park money short-term; withdraw anytime.',
    color: '#14B8A6',
    icon: 'droplet',
  },
];

const QUICK_AMOUNTS = [1000, 2500, 5000, 10000, 25000];

// ── Helpers ───────────────────────────────────────────────────────────────────
const titleCase = (s: string): string =>
  s ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : s;

const mapAccount = (a: AccountResponse): AccountVM => ({
  accountId: a.account_id,
  bankName: a.bank_name,
  accountType: titleCase(String(a.account_type)),
  accountNumberMasked: a.account_number_masked,
  balance: Number(a.balance) || 0,
});

const formatCurrency = (n: number) => '₹' + n.toLocaleString('en-IN');

const RISK_COLORS: Record<FundVM['risk'], string> = {
  Low: COLORS.success,
  Moderate: '#F59E0B',
  High: '#EF4444',
};

// ── Account selector ──────────────────────────────────────────────────────────
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
        <View style={styles.flex1}>
          <Text style={styles.accountCardTitle}>
            {selected.bankName} {'·'} {selected.accountType}
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

      {expanded &&
        accounts
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
              <View style={styles.flex1}>
                <Text style={styles.accountCardTitle}>
                  {acc.bankName} {'·'} {acc.accountType}
                </Text>
                <Text style={styles.accountCardSub}>{acc.accountNumberMasked}</Text>
              </View>
              <Text style={styles.accountCardBalance}>{formatCurrency(acc.balance)}</Text>
            </TouchableOpacity>
          ))}
    </View>
  );
};

// ── Fund card ─────────────────────────────────────────────────────────────────
const FundCard = ({
  fund,
  selected,
  onPress,
}: {
  fund: FundVM;
  selected: boolean;
  onPress: () => void;
}) => (
  <TouchableOpacity
    style={[styles.fundCard, selected && styles.fundCardSelected]}
    onPress={onPress}
    activeOpacity={0.75}
  >
    <View style={[styles.fundIconWrap, { backgroundColor: fund.color + '22' }]}>
      <Feather name={fund.icon as any} size={18} color={fund.color} />
    </View>
    <View style={styles.flex1}>
      <Text style={styles.fundName}>{fund.name}</Text>
      <Text style={styles.fundBlurb}>{fund.blurb}</Text>
      <View style={styles.fundMetaRow}>
        <Text style={styles.fundCategory}>{fund.categoryLabel}</Text>
        <View style={[styles.riskPill, { backgroundColor: RISK_COLORS[fund.risk] + '22' }]}>
          <Text style={[styles.riskPillText, { color: RISK_COLORS[fund.risk] }]}>
            {fund.risk} risk
          </Text>
        </View>
      </View>
    </View>
    <View style={[styles.radio, selected && styles.radioSelected]}>
      {selected && <Feather name="check" size={12} color={COLORS.textOnDark} />}
    </View>
  </TouchableOpacity>
);

// ── Screen ────────────────────────────────────────────────────────────────────
const TransactionInitiateScreen = ({ navigation, route }: any) => {
  const { t } = useI18n();
  // Task 4.11 — arriving from "Start this" on a wealth recommendation.
  // We pre-select the closest matching fund and amount, but change nothing
  // else: the customer still confirms, and the security pipeline still runs.
  const prefill = route?.params?.prefill as
    | { amount?: number; fundCategory?: string; fundName?: string; source?: string }
    | undefined;
  const [accounts, setAccounts] = useState<AccountVM[]>([]);
  const [loadingAccounts, setLoadingAccounts] = useState(true);
  const [accountsError, setAccountsError] = useState<string | null>(null);

  const [fromAccountId, setFromAccountId] = useState<string>('');
  const [selectedFundId, setSelectedFundId] = useState<string | null>(() => {
    if (!prefill) return null;
    const byCategory = FUNDS.find((f) => f.category === prefill.fundCategory);
    const byName = FUNDS.find(
      (f) => prefill.fundName && f.name.toLowerCase() === prefill.fundName.toLowerCase()
    );
    return (byName || byCategory)?.id ?? null;
  });
  const [amount, setAmount] = useState(
    prefill?.amount && prefill.amount > 0 ? String(Math.round(prefill.amount)) : ''
  );
  const [submitting, setSubmitting] = useState(false);

  const loadAccounts = useCallback(async () => {
    setAccountsError(null);
    setLoadingAccounts(true);
    try {
      const list = await api.getAccounts();
      // Investments are funded from Savings accounts only (task 2.3).
      const mapped = (list || [])
        .map(mapAccount)
        .filter((a) => a.accountType.toUpperCase() === 'SAVINGS');
      setAccounts(mapped);
      if (mapped.length > 0) setFromAccountId(mapped[0].accountId);
    } catch (e) {
      const err = e as ApiError;
      setAccountsError(
        err instanceof ApiError && err.isConnectivityError
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
  const selectedFund = FUNDS.find((f) => f.id === selectedFundId) || null;
  const numericAmount = Number(amount) || 0;

  const handleSubmit = () => {
    if (!fromAccount) {
      Alert.alert('No account selected', 'Please choose a Savings account to invest from.');
      return;
    }
    if (!selectedFund) {
      Alert.alert('Choose a fund', 'Please select the mutual fund you want to invest in.');
      return;
    }
    if (numericAmount <= 0) {
      Alert.alert('Enter an amount', 'Please enter how much you want to invest.');
      return;
    }
    if (numericAmount > fromAccount.balance) {
      Alert.alert(
        'Not enough balance',
        `Your ${fromAccount.accountType} account has ${formatCurrency(
          fromAccount.balance
        )} available.`
      );
      return;
    }

    setSubmitting(true);

    // Same contract keys SecurityReview already consumes.
    const transactionData = {
      amount: numericAmount,
      fromAccountId: fromAccount.accountId,
      channel: 'UPI',
      fromAccount: {
        masked: fromAccount.accountNumberMasked,
        bankName: fromAccount.bankName,
        accountType: fromAccount.accountType,
      },
      toLabel: selectedFund.name,
      toDetail: selectedFund.categoryLabel,
      fundCategory: selectedFund.category,
      paymentMode: 'Investment',
      note: '',
      isNewRecipient: false,
      timestamp: new Date().toISOString(),
    };

    setTimeout(() => {
      setSubmitting(false);
      navigation.navigate('SecurityReview', { transactionData });
    }, 250);
  };

  if (loadingAccounts) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.centerText}>Loading your accounts{'…'}</Text>
      </View>
    );
  }

  if (accountsError || accounts.length === 0) {
    return (
      <View style={styles.centerContainer}>
        <Feather
          name={accountsError ? 'wifi-off' : 'credit-card'}
          size={28}
          color={COLORS.textTertiary}
        />
        <Text style={styles.centerText}>
          {accountsError || 'No Savings account available to invest from.'}
        </Text>
        {accountsError && (
          <TouchableOpacity style={styles.retryBtn} onPress={loadAccounts} activeOpacity={0.8}>
            <Feather name="refresh-cw" size={16} color={COLORS.textOnDark} />
            <Text style={styles.retryBtnText}>{t('common.tryAgain')}</Text>
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
            {t('invest.trustBanner')}
          </Text>
        </View>

        {/* From account */}
        <AccountSelector
          accounts={accounts}
          selectedId={fromAccountId}
          onSelect={setFromAccountId}
          label={t('invest.from')}
        />

        {/* Fund selection */}
        <View style={styles.fieldGroup}>
          <Text style={styles.fieldLabel}>{t('invest.chooseFund')}</Text>
          {FUNDS.map((fund) => (
            <FundCard
              key={fund.id}
              fund={fund}
              selected={fund.id === selectedFundId}
              onPress={() =>
                setSelectedFundId((prev) => (prev === fund.id ? null : fund.id))
              }
            />
          ))}
        </View>

        {/* Amount */}
        <View style={styles.fieldGroup}>
          <Text style={styles.fieldLabel}>{t('invest.amount')}</Text>
          <View style={styles.amountRow}>
            <Text style={styles.rupee}>{'₹'}</Text>
            <TextInput
              style={styles.amountInput}
              value={amount}
              onChangeText={(t) => setAmount(t.replace(/[^\d]/g, ''))}
              keyboardType="number-pad"
              placeholder="0"
              placeholderTextColor={COLORS.textTertiary}
              maxLength={8}
            />
          </View>
          <View style={styles.chipsRow}>
            {QUICK_AMOUNTS.map((q) => (
              <TouchableOpacity
                key={q}
                style={[styles.chip, numericAmount === q && styles.chipActive]}
                onPress={() => setAmount(String(q))}
                activeOpacity={0.7}
              >
                <Text
                  style={[styles.chipText, numericAmount === q && styles.chipTextActive]}
                >
                  {formatCurrency(q)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Summary + CTA */}
        {selectedFund && numericAmount > 0 && (
          <View style={styles.summaryCard}>
            <Text style={styles.summaryText}>
              {t('invest.investingAmt')} <Text style={styles.summaryBold}>{formatCurrency(numericAmount)}</Text>{' '}
              in <Text style={styles.summaryBold}>{selectedFund.name}</Text>
            </Text>
          </View>
        )}

        <TouchableOpacity
          style={[
            styles.submitBtn,
            (!selectedFund || numericAmount <= 0 || submitting) && styles.submitBtnDisabled,
          ]}
          onPress={handleSubmit}
          disabled={!selectedFund || numericAmount <= 0 || submitting}
          activeOpacity={0.85}
        >
          {submitting ? (
            <ActivityIndicator color={COLORS.textOnDark} />
          ) : (
            <>
              <Feather name="shield" size={18} color={COLORS.textOnDark} />
              <Text style={styles.submitBtnText}>{t('invest.cta')}</Text>
            </>
          )}
        </TouchableOpacity>

        <Text style={styles.disclaimer}>
          {t('invest.disclaimer')}
        </Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  scrollContent: { padding: SPACING.lg, paddingBottom: SPACING.xxl },
  flex1: { flex: 1 },

  centerContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.background,
    padding: SPACING.xl,
  },
  centerText: {
    ...TYPOGRAPHY.body,
    color: COLORS.textSecondary,
    marginTop: SPACING.md,
    textAlign: 'center',
  },
  retryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
    marginTop: SPACING.lg,
    backgroundColor: COLORS.primary,
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.sm,
    borderRadius: BORDER_RADIUS.md,
  },
  retryBtnText: { ...TYPOGRAPHY.bodyMedium, color: COLORS.textOnDark },

  trustBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    backgroundColor: COLORS.primaryVeryLight,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
  },
  trustBannerText: { ...TYPOGRAPHY.caption, color: COLORS.primaryDark, flex: 1 },

  fieldGroup: { marginBottom: SPACING.lg },
  fieldLabel: {
    ...TYPOGRAPHY.captionBold,
    color: COLORS.textSecondary,
    marginBottom: SPACING.sm,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
  },

  accountCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: SPACING.md,
    gap: SPACING.md,
  },
  accountListItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.md,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: SPACING.md,
    gap: SPACING.md,
    marginTop: SPACING.xs,
  },
  accountIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: COLORS.primaryVeryLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  accountCardTitle: { ...TYPOGRAPHY.bodyMedium, color: COLORS.text },
  accountCardSub: { ...TYPOGRAPHY.caption, color: COLORS.textTertiary },
  accountBalanceWrap: { alignItems: 'flex-end', gap: 2 },
  accountCardBalance: { ...TYPOGRAPHY.bodyMedium, color: COLORS.primary },

  fundCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    padding: SPACING.md,
    gap: SPACING.md,
    marginBottom: SPACING.sm,
  },
  fundCardSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primaryVeryLight,
    ...SHADOWS.small,
  },
  fundIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  fundName: { ...TYPOGRAPHY.bodyMedium, color: COLORS.text },
  fundBlurb: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary, marginTop: 1 },
  fundMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginTop: SPACING.xs,
  },
  fundCategory: { ...TYPOGRAPHY.caption, color: COLORS.textTertiary },
  riskPill: {
    paddingHorizontal: SPACING.sm,
    paddingVertical: 2,
    borderRadius: 999,
  },
  riskPillText: { fontSize: 10, fontWeight: '700' },
  radio: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: COLORS.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioSelected: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },

  amountRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
    paddingHorizontal: SPACING.lg,
  },
  rupee: { ...TYPOGRAPHY.h2, color: COLORS.textSecondary, marginRight: SPACING.xs },
  amountInput: { ...TYPOGRAPHY.h1, color: COLORS.text, flex: 1, paddingVertical: SPACING.md },
  chipsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: SPACING.sm, marginTop: SPACING.sm },
  chip: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.xs,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: COLORS.border,
    backgroundColor: COLORS.surface,
  },
  chipActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  chipText: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary },
  chipTextActive: { color: COLORS.textOnDark, fontWeight: '700' },

  summaryCard: {
    backgroundColor: COLORS.primaryVeryLight,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.md,
  },
  summaryText: { ...TYPOGRAPHY.body, color: COLORS.primaryDark },
  summaryBold: { fontWeight: '800' },

  submitBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.sm,
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.lg,
    paddingVertical: SPACING.md + 2,
    ...SHADOWS.medium,
  },
  submitBtnDisabled: { opacity: 0.45 },
  submitBtnText: { ...TYPOGRAPHY.bodyMedium, color: COLORS.textOnDark, fontSize: 16 },

  disclaimer: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    textAlign: 'center',
    marginTop: SPACING.lg,
    lineHeight: 16,
  },
});

export default TransactionInitiateScreen;
