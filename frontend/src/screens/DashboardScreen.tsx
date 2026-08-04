// src/screens/DashboardScreen.tsx
// SecureWealth Twin — Home Dashboard
//
// BACKEND INTEGRATION (was 3 mock JSON imports):
//  • Single source: GET /dashboard/  → user + accounts + recent_transactions + net_worth.
//  • Backend (snake_case) is mapped to the existing component shapes so NONE of the
//    sub-components (AccountCard, TransactionRow, etc.) changed.
//  • Transaction `decision` is now real (ALLOW/WARN/CHALLENGE/BLOCK) → badges use it.
//  • Removed: Primary badge (no field in API), last-login line (not in dashboard payload).
//  • Minimal loading + error + empty states added; layout/styles otherwise unchanged.
//  • Pull-to-refresh now re-fetches the dashboard.

import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Dimensions,
  NativeSyntheticEvent,
  NativeScrollEvent,
  StatusBar,
  ActivityIndicator,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { COLORS } from '../constants/colors';
import { useFocusEffect } from '@react-navigation/native';
import { useI18n } from '../i18n';
import { DashboardSkeleton } from '../components/common/Skeleton';
import {
  SPACING,
  TYPOGRAPHY,
  BORDER_RADIUS,
  SHADOWS,
  CARD,
  ANIMATION,
} from '../constants/theme';
import GlossaryPopup from '../components/common/GlossaryPopup';
import { api, ApiError } from '../api/apiService';
import type { AccountResponse, TransactionResponse } from '../api/types';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const CARD_WIDTH = SCREEN_WIDTH - SPACING.lg * 2; // Full width minus horizontal padding

// ── View-model shapes (what the UI components expect) ─────────────────────────
// We adapt the backend payloads into these so the render code stays identical.
interface AccountVM {
  accountId: string;
  bankName: string;
  accountType: string;       // "Savings" | "Current" | "Salary" (title-case for GlossaryPopup)
  accountNumberMasked: string;
  balance: number;
  isPrimary: boolean;        // always false now (no API field)
}
interface TransactionVM {
  transactionId: string;
  merchantName: string;
  merchantCategory: string;
  transactionTime: string;
  channel: string;
  amount: number;            // signed: negative = debit, positive = credit
  decision: string | null;   // ALLOW | WARN | CHALLENGE | BLOCK | null
}

// ── Mappers: backend → view-model ─────────────────────────────────────────────
const titleCase = (s: string): string =>
  s ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : s;

const mapAccount = (a: AccountResponse): AccountVM => ({
  accountId: a.account_id,
  bankName: a.bank_name,
  accountType: titleCase(String(a.account_type)),
  accountNumberMasked: a.account_number_masked,
  balance: Number(a.balance) || 0,
  isPrimary: false,
});

// The backend amount is a positive decimal. We infer credit vs debit from the
// merchant category ("Income"/"Salary" = credit) so the existing +/- and colour
// logic keeps working. Adjust this rule if your backend encodes direction elsewhere.
const CREDIT_CATEGORIES = new Set(['income', 'salary', 'refund', 'credit', 'interest']);
const mapTransaction = (t: TransactionResponse): TransactionVM => {
  const cat = String(t.fund_category || '').toLowerCase();
  const isCredit = CREDIT_CATEGORIES.has(cat);
  const magnitude = Math.abs(Number(t.amount) || 0);
  return {
    transactionId: t.transaction_id,
    merchantName: t.fund_name,
    merchantCategory: t.fund_category,
    transactionTime: t.transaction_time,
    channel: String(t.channel),
    amount: isCredit ? magnitude : -magnitude,
    decision: (t.decision as string) ?? null,
  };
};

// ── Helpers ───────────────────────────────────────────────────────────────────
const formatCurrency = (amount: number): string => {
  const abs = Math.abs(amount);
  return '\u20B9' + abs.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

const getGreeting = (): string => {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
};

const firstNameOf = (fullName: string): string => {
  if (!fullName) return 'there';
  return fullName.trim().split(/\s+/)[0];
};

const formatTransactionTime = (isoString: string): string => {
  const txDate = new Date(isoString);
  const now = new Date();
  const todayStr = now.toDateString();
  const txStr = txDate.toDateString();
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);

  if (txStr === todayStr) return 'Today';
  if (txStr === yesterday.toDateString()) return 'Yesterday';
  return txDate.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
};

// Category → icon mapping
const getCategoryIcon = (category: string): string => {
  const map: Record<string, string> = {
    Shopping: 'shopping-bag',
    Income: 'trending-up',
    Utilities: 'zap',
    Transfer: 'send',
    'Food & Dining': 'coffee',
    Travel: 'map-pin',
    Health: 'heart',
    Entertainment: 'film',
  };
  return map[category] || 'circle';
};

const getCategoryColor = (category: string): string => {
  const map: Record<string, string> = {
    Shopping: '#6366F1',
    Income: COLORS.success,
    Utilities: '#F59E0B',
    Transfer: COLORS.primary,
    'Food & Dining': '#EF4444',
    Travel: '#06B6D4',
    Health: '#EC4899',
    Entertainment: '#8B5CF6',
  };
  return map[category] || COLORS.textTertiary;
};

// ── Sub-components ────────────────────────────────────────────────────────────

// Account Card — single slide in the carousel
// All three card actions were rendered without an onPress, so tapping them did
// nothing at all — no navigation, no feedback. A control that looks pressable
// and silently ignores the press reads as a broken app, which is the last
// impression this screen should give.
const AccountCard = ({
  account,
  onInvest,
  onStatement,
  onRefresh,
}: {
  account: AccountVM;
  onInvest: () => void;
  onStatement: () => void;
  onRefresh: () => void;
}) => {
  const { t } = useI18n();
  const [balanceVisible, setBalanceVisible] = useState(true);

  // Color per bank
  const isPSB = account.bankName.includes('Punjab');
  const cardBg = isPSB ? COLORS.primaryDark : '#1B3A6B'; // PSB dark green vs SBI dark blue
  const accentBar = isPSB ? COLORS.accent : '#3B82F6';

  return (
    <View style={[styles.accountCard, { backgroundColor: cardBg, width: CARD_WIDTH }]}>
      {/* Decorative top accent strip */}
      <View style={[styles.accountCardAccent, { backgroundColor: accentBar }]} />

      {/* Bank name + account type */}
      <View style={styles.accountCardHeader}>
        <View>
          <Text style={styles.accountBankName}>{account.bankName}</Text>
          <View style={styles.accountTypeRow}>
            <Text style={styles.accountType}>{account.accountType} A/c</Text>
            <GlossaryPopup term={
              account.accountType === 'Savings' ? 'SAVINGS_ACCOUNT'
              : account.accountType === 'Current' ? 'CURRENT_ACCOUNT'
              : 'SALARY_ACCOUNT'
            }>
              <Feather name="help-circle" size={13} color={COLORS.textOnDarkSub} />
            </GlossaryPopup>
          </View>
        </View>
        {/* Primary badge removed — no field in API */}
      </View>

      {/* Masked account number */}
      <Text style={styles.accountNumber}>{account.accountNumberMasked}</Text>

      {/* Balance row */}
      <View style={styles.balanceRow}>
        <View>
          <Text style={styles.balanceLabel}>{t('dash.availableBalance')}</Text>
          <Text style={styles.balanceAmount}>
            {balanceVisible ? formatCurrency(account.balance) : '\u20B9 \u2022\u2022\u2022\u2022\u2022\u2022'}
          </Text>
        </View>
        <TouchableOpacity
          onPress={() => setBalanceVisible(!balanceVisible)}
          style={styles.eyeBtn}
          activeOpacity={0.7}
          hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
          accessibilityRole="button"
          accessibilityLabel={
            balanceVisible ? t('a11y.hideBalance') : t('a11y.showBalance')
          }
        >
          <Feather
            name={balanceVisible ? 'eye' : 'eye-off'}
            size={20}
            color={COLORS.textOnDarkSub}
          />
        </TouchableOpacity>
      </View>

      {/* Quick action buttons on card */}
      <View style={styles.cardActions}>
        <TouchableOpacity
          style={styles.cardActionBtn}
          onPress={onInvest}
          activeOpacity={0.7}
          accessibilityRole="button"
          accessibilityLabel={t('common.invest')}
        >
          <Feather name="trending-up" size={14} color={COLORS.textOnDark} />
          <Text style={styles.cardActionText}>{t('common.invest')}</Text>
        </TouchableOpacity>
        <View style={styles.cardActionDivider} />
        {/* Statement opens the activity history — every investment with the
            security decision that was taken on it. This app only moves money
            into mutual funds, so that history IS the statement. */}
        <TouchableOpacity
          style={styles.cardActionBtn}
          onPress={onStatement}
          activeOpacity={0.7}
          accessibilityRole="button"
          accessibilityLabel={t('dash.statement')}
        >
          <Feather name="file-text" size={14} color={COLORS.textOnDark} />
          <Text style={styles.cardActionText}>{t('dash.statement')}</Text>
        </TouchableOpacity>
        <View style={styles.cardActionDivider} />
        <TouchableOpacity
          style={styles.cardActionBtn}
          onPress={onRefresh}
          activeOpacity={0.7}
          accessibilityRole="button"
          accessibilityLabel={t('common.refresh')}
        >
          <Feather name="refresh-cw" size={14} color={COLORS.textOnDark} />
          <Text style={styles.cardActionText}>{t('common.refresh')}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

// Dot indicators for the carousel
const CarouselDots = ({ count, active }: { count: number; active: number }) => (
  <View style={styles.dotsRow}>
    {Array.from({ length: count }).map((_, i) => (
      <View
        key={i}
        style={[
          styles.dot,
          i === active ? styles.dotActive : styles.dotInactive,
        ]}
      />
    ))}
  </View>
);

// Protection Status card — replaces the old confusing "security status"
// Live protection signals.
//
// This card used to list "iPhone 14 Pro, Delhi / Daytime activity / Regular
// spending pattern" — all three hardcoded and always green, regardless of the
// customer's actual state. It claimed a device we never checked and a location
// we never had. Every row below is now derived from something real: the
// registered device list, the actual clock, and the customer's own recent
// security decisions.
const ProtectionStatusCard = () => {
  const { t } = useI18n();
  const [device, setDevice] = useState<{ name: string; trusted: boolean } | null>(null);
  const [flagged, setFlagged] = useState<number | null>(null);

  useEffect(() => {
    let active = true;
    api
      .getDevices()
      .then((list) => {
        if (!active || !list?.length) return;
        const d = list[0];
        setDevice({
          name: d.device_name,
          trusted: String(d.trust_status).toUpperCase() === 'TRUSTED',
        });
      })
      .catch(() => undefined);
    api
      .getMySecurityActivity()
      .then((res) => {
        if (!active) return;
        const recent = (res.activities || []).slice(0, 10);
        setFlagged(
          recent.filter((a: any) => a.decision === 'CHALLENGE' || a.decision === 'BLOCK')
            .length
        );
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, []);

  const hour = new Date().getHours();
  const daytime = hour >= 6 && hour < 22;

  const signals = [
    device && {
      icon: 'smartphone',
      label: `${device.name} · ${
        device.trusted ? t('dash.deviceRecognised') : t('dash.deviceNew')
      }`,
      ok: device.trusted,
    },
    {
      icon: daytime ? 'sun' : 'moon',
      label: daytime ? t('dash.daytime') : t('dash.lateNight'),
      ok: daytime,
    },
    flagged !== null && {
      icon: 'activity',
      label: flagged === 0 ? t('dash.noRecentFlags') : t('dash.recentFlags'),
      ok: flagged === 0,
    },
  ].filter(Boolean) as { icon: string; label: string; ok: boolean }[];

  return (
    <View style={styles.protectionCard}>
      {/* Header */}
      <View style={styles.protectionHeader}>
        <View style={styles.protectionIconWrap}>
          <Feather name="shield" size={18} color={COLORS.success} />
        </View>
        <View style={{ flex: 1, marginLeft: SPACING.sm }}>
          <Text style={styles.protectionTitle}>{t('dash.protectedTitle')}</Text>
          <Text style={styles.protectionSub}>{t('dash.allSystems')}</Text>
        </View>
        {/* Animated pulse dot */}
        <View style={styles.pulseDotOuter}>
          <View style={styles.pulseDotInner} />
        </View>
      </View>

      {/* Signal list */}
      <View style={styles.signalList}>
        {signals.map((s, i) => (
          <View key={i} style={styles.signalRow}>
            <Feather
              name={s.icon as any}
              size={14}
              color={s.ok ? COLORS.textSecondary : COLORS.danger}
            />
            <Text style={styles.signalLabel}>{s.label}</Text>
            <Feather
              name={s.ok ? 'check' : 'x'}
              size={14}
              color={s.ok ? COLORS.success : COLORS.danger}
            />
          </View>
        ))}
      </View>

      {/* Footer hint */}
      <View style={styles.protectionFooter}>
        <Feather name="info" size={12} color={COLORS.textTertiary} />
        <Text style={styles.protectionFooterText}>
          {t('dash.protectedSub')}
        </Text>
      </View>
    </View>
  );
};

// Transaction row
const TransactionRow = ({ txn }: { txn: TransactionVM }) => {
  const { t } = useI18n();
  const isCredit = txn.amount > 0;
  const isBlocked = txn.decision === 'BLOCK';
  const isWarn = txn.decision === 'WARN' || txn.decision === 'CHALLENGE';
  const iconName = getCategoryIcon(txn.merchantCategory);
  const iconColor = isBlocked ? COLORS.danger : getCategoryColor(txn.merchantCategory);

  return (
    <TouchableOpacity style={styles.txnRow} activeOpacity={0.7}>
      {/* Icon */}
      <View style={[styles.txnIcon, { backgroundColor: iconColor + '18' }]}>
        <Feather name={iconName as any} size={18} color={iconColor} />
      </View>

      {/* Details */}
      <View style={styles.txnDetails}>
        <Text style={styles.txnName} numberOfLines={1}>{txn.merchantName}</Text>
        <View style={styles.txnMeta}>
          <Text style={styles.txnDate}>{formatTransactionTime(txn.transactionTime)}</Text>
          {/* Channel badge */}
          <View style={styles.channelBadge}>
            <Text style={styles.channelText}>{txn.channel}</Text>
          </View>
          {/* Blocked/Warn badge */}
          {isBlocked && (
            <View style={styles.blockedBadge}>
              <Feather name="shield" size={10} color={COLORS.danger} />
              <Text style={styles.blockedText}>{t('dash.stopped')}</Text>
            </View>
          )}
          {isWarn && !isBlocked && (
            <View style={styles.warnBadge}>
              <Feather name="alert-triangle" size={10} color={COLORS.caution} />
              <Text style={styles.warnBadgeText}>{t('dash.flagged')}</Text>
            </View>
          )}
        </View>
      </View>

      {/* Amount */}
      <Text
        style={[
          styles.txnAmount,
          {
            color: isBlocked
              ? COLORS.textTertiary
              : isCredit
              ? COLORS.success
              : COLORS.text,
          },
        ]}
      >
        {isBlocked
          ? '\u2014'
          : `${isCredit ? '+' : '-'}${formatCurrency(txn.amount)}`}
      </Text>
    </TouchableOpacity>
  );
};

// Wealth Tip card — single line from the wealth engine
// Wealth tip — the customer's real savings rate and the wealth engine's own
// top recommendation.
//
// This previously showed a fixed sentence: "Your savings rate is 65% this month
// — consider opening a Fixed Deposit." The 65% was invented and the advice was
// the same for every customer and every month. If we cannot get real numbers
// now, the card renders nothing rather than making some up.
const WealthTipCard = ({ onPress }: { onPress?: () => void }) => {
  const { t } = useI18n();
  const [tip, setTip] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const cashflow = await api.getCashflow();
        const income = Number(cashflow?.total_income) || 0;
        const net = Number(cashflow?.net_cashflow) || 0;
        if (!active || income <= 0) return;
        const pct = Math.max(0, Math.round((net / income) * 100));
        setTip(t('dash.savingsRate').replace('{pct}', String(pct)));
      } catch {
        // Consent not granted or aggregation unavailable — show nothing.
      }
    })();
    return () => {
      active = false;
    };
  }, [t]);

  if (!tip) return null;

  return (
    <TouchableOpacity
      style={styles.tipCard}
      onPress={onPress}
      activeOpacity={onPress ? 0.8 : 1}
      disabled={!onPress}
    >
      <View style={styles.tipIconWrap}>
        <Feather name="trending-up" size={18} color={COLORS.accent} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={styles.tipLabel}>{t('dash.smartTip')}</Text>
        <Text style={styles.tipText}>{tip}</Text>
      </View>
      {onPress ? (
        <View style={styles.tipArrow}>
          <Feather name="chevron-right" size={18} color={COLORS.accent} />
        </View>
      ) : null}
    </TouchableOpacity>
  );
};

// ── Main Screen ───────────────────────────────────────────────────────────────
const DashboardScreen = ({ navigation }: any) => {
  const { t } = useI18n();
  const insets = useSafeAreaInsets();
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeCardIndex, setActiveCardIndex] = useState(0);
  const carouselRef = useRef<ScrollView>(null);

  // Live data (mapped to view-model shapes)
  const [firstName, setFirstName] = useState('there');
  const [accounts, setAccounts] = useState<AccountVM[]>([]);
  const [transactions, setTransactions] = useState<TransactionVM[]>([]);

  const loadDashboard = useCallback(async () => {
    setError(null);
    try {
      const dash = await api.getDashboard();
      setFirstName(firstNameOf(dash.user?.full_name || ''));
      setAccounts((dash.accounts || []).map(mapAccount));
      setTransactions((dash.recent_transactions || []).map(mapTransaction));
    } catch (e) {
      const err = e as ApiError;
      setError(
        err instanceof ApiError && err.isConnectivityError
          ? 'Cannot reach the server. Pull down to retry.'
          : 'Could not load your dashboard. Pull down to retry.'
      );
    }
  }, []);

  // Initial load
  useEffect(() => {
    (async () => {
      setLoading(true);
      await loadDashboard();
      setLoading(false);
    })();
  }, [loadDashboard]);

  // Balance and recent activity change as soon as an investment settles, so
  // bring the tab up to date every time it regains focus. Silent refresh: the
  // first focus is skipped because the initial load has just run.
  const firstFocus = useRef(true);
  useFocusEffect(
    useCallback(() => {
      if (firstFocus.current) {
        firstFocus.current = false;
        return;
      }
      loadDashboard();
    }, [loadDashboard])
  );

  // Wealth-first quick actions (task 1.2: Send → Invest)
  const quickActions = [
    {
      id: '1',
      title: 'Invest',
      icon: 'trending-up',
      color: COLORS.primary,
      onPress: () =>
        navigation.navigate('WealthTab', { screen: 'TransactionInitiate' }),
    },
    {
      id: '2',
      title: 'My Wealth',
      icon: 'pie-chart',
      color: '#6366F1',
      onPress: () => navigation.navigate('WealthTab'),
    },
    {
      id: '3',
      title: 'Phishing Check',
      icon: 'message-square',
      color: '#F59E0B',
      onPress: () => navigation.navigate('PhishingTab'),
    },
    {
      id: '4',
      title: 'Security',
      icon: 'shield',
      color: COLORS.success,
      onPress: () => navigation.navigate('SafetyTab'),
    },
  ];

  // Total balance across all accounts
  const totalBalance = accounts.reduce((sum, acc) => sum + acc.balance, 0);

  // Recent 5 transactions, most recent first
  const recentTxns = [...transactions]
    .sort((a, b) => new Date(b.transactionTime).getTime() - new Date(a.transactionTime).getTime())
    .slice(0, 5);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadDashboard();
    setRefreshing(false);
  }, [loadDashboard]);

  const handleCarouselScroll = (e: NativeSyntheticEvent<NativeScrollEvent>) => {
    const index = Math.round(e.nativeEvent.contentOffset.x / CARD_WIDTH);
    setActiveCardIndex(Math.max(0, Math.min(index, Math.max(0, accounts.length - 1))));
  };

  // ── Initial load: skeleton, not a spinner ──
  if (loading) {
    return (
      <>
        <StatusBar barStyle="light-content" backgroundColor={COLORS.primaryDark} />
        <DashboardSkeleton />
      </>
    );
  }

  return (
    <>
      <StatusBar barStyle="light-content" backgroundColor={COLORS.primaryDark} />
      <ScrollView
        style={styles.container}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={COLORS.textOnDark}
            colors={[COLORS.primary]}
          />
        }
      >
        {/* ── Hero section (green background continues from nav header) ── */}
        <View style={styles.hero}>
          {/* Greeting */}
          <View style={styles.greetingRow}>
            <View>
              <Text style={styles.greeting}>
                {getGreeting()}, {firstName}!
              </Text>
              {/* last-login line removed — not in dashboard payload */}
            </View>
            {/* Total across all accounts — shown in hero */}
            <View style={styles.totalWrap}>
              <Text style={styles.totalLabel}>Total</Text>
              <Text style={styles.totalAmount}>{formatCurrency(totalBalance)}</Text>
            </View>
          </View>

          {/* Error banner (data failed but we still render the shell) */}
          {error && (
            <View style={styles.errorBanner}>
              <Feather name="wifi-off" size={14} color={COLORS.textOnDark} />
              <Text style={styles.errorBannerText}>{error}</Text>
            </View>
          )}

          {/* Account card carousel */}
          {accounts.length > 0 ? (
            <>
              <ScrollView
                ref={carouselRef}
                horizontal
                pagingEnabled
                showsHorizontalScrollIndicator={false}
                onMomentumScrollEnd={handleCarouselScroll}
                decelerationRate="fast"
                snapToInterval={CARD_WIDTH}
                contentContainerStyle={styles.carouselContent}
                style={styles.carousel}
              >
                {accounts.map((account) => (
                  <AccountCard
                    key={account.accountId}
                    account={account}
                    onInvest={() =>
                      navigation.navigate('WealthTab', { screen: 'TransactionInitiate' })
                    }
                    onStatement={() =>
                      navigation.navigate('SafetyTab', { screen: 'MySecurityActivity' })
                    }
                    onRefresh={handleRefresh}
                  />
                ))}
              </ScrollView>

              {/* Dot indicators */}
              <CarouselDots count={accounts.length} active={activeCardIndex} />
            </>
          ) : (
            !error && (
              <View style={styles.emptyAccounts}>
                <Feather name="credit-card" size={22} color={COLORS.textOnDarkSub} />
                <Text style={styles.emptyAccountsText}>{t('dash.noAccounts')}</Text>
              </View>
            )
          )}
        </View>

        {/* ── Content area (white/light background) ── */}
        <View style={styles.content}>

          {/* Quick Actions — single horizontal row like PSB app */}
          <View style={styles.quickActionsSection}>
            {quickActions.map((action) => (
              <TouchableOpacity
                key={action.id}
                style={styles.quickAction}
                onPress={action.onPress}
                activeOpacity={0.7}
              >
                <View style={[styles.quickActionIcon, { backgroundColor: action.color + '15' }]}>
                  <Feather name={action.icon as any} size={22} color={action.color} />
                </View>
                <Text style={styles.quickActionLabel}>{action.title}</Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Divider */}
          <View style={styles.sectionDivider} />

          {/* Protection Status */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>{t('dash.accountProtection')}</Text>
            <ProtectionStatusCard />
          </View>

          {/* Divider */}
          <View style={styles.sectionDivider} />

          {/* Recent Transactions */}
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>{t('dash.recentTxns')}</Text>
              <TouchableOpacity activeOpacity={0.7}>
                <Text style={styles.viewAllText}>{t('dash.viewAll')}</Text>
              </TouchableOpacity>
            </View>

            {recentTxns.length > 0 ? (
              recentTxns.map((txn) => (
                <TransactionRow key={txn.transactionId} txn={txn} />
              ))
            ) : (
              <Text style={styles.emptyTxnText}>{t('dash.noTxns')}</Text>
            )}
          </View>

          {/* Divider */}
          <View style={styles.sectionDivider} />

          {/* Smart Wealth Tip */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>{t('dash.wealthInsight')}</Text>
            <WealthTipCard onPress={() => navigation.navigate('WealthTab')} />
          </View>

          {/* Bottom padding so last card doesn't sit on tab bar */}
          <View style={{ height: SPACING.xxl }} />
        </View>
      </ScrollView>
    </>
  );
};

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.primaryDark, // Hero bg = same as header
  },

  // ── Loading / states ──────────────────────────────────────────────────────
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
    gap: SPACING.md,
  },
  loadingText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginHorizontal: SPACING.lg,
    marginBottom: SPACING.md,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    backgroundColor: 'rgba(255,255,255,0.12)',
    borderRadius: BORDER_RADIUS.md,
  },
  errorBannerText: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textOnDark,
    flex: 1,
  },
  emptyAccounts: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.sm,
    marginHorizontal: SPACING.lg,
    paddingVertical: SPACING.xxl,
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: BORDER_RADIUS.xl,
  },
  emptyAccountsText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textOnDarkSub,
  },
  emptyTxnText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textTertiary,
    paddingVertical: SPACING.md,
  },

  // ── Hero ──────────────────────────────────────────────────────────────────
  hero: {
    backgroundColor: COLORS.primaryDark,
    paddingBottom: SPACING.lg,
  },
  greetingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingHorizontal: SPACING.lg,
    paddingTop: SPACING.md,
    paddingBottom: SPACING.lg,
  },
  greeting: {
    ...TYPOGRAPHY.h3,
    color: COLORS.textOnDark,
    fontWeight: '700',
  },
  lastLogin: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textOnDarkSub,
    marginTop: 2,
  },
  totalWrap: {
    alignItems: 'flex-end',
  },
  totalLabel: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textOnDarkSub,
  },
  totalAmount: {
    ...TYPOGRAPHY.h4,
    color: COLORS.accent,
    fontWeight: '700',
  },

  // ── Carousel ──────────────────────────────────────────────────────────────
  carousel: {
    // Full width, cards sized by CARD_WIDTH
  },
  carouselContent: {
    paddingHorizontal: SPACING.lg,
    gap: SPACING.lg,
  },
  accountCard: {
    borderRadius: BORDER_RADIUS.xl,
    padding: SPACING.lg,
    overflow: 'hidden',
    ...SHADOWS.large,
  },
  accountCardAccent: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 3,
  },
  accountCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: SPACING.sm,
    marginTop: SPACING.xs,
  },
  accountBankName: {
    ...TYPOGRAPHY.label,
    color: COLORS.textOnDarkSub,
    fontWeight: '600',
  },
  accountTypeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
    marginTop: 2,
  },
  accountType: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textOnDarkSub,
  },
  primaryBadge: {
    backgroundColor: COLORS.accent + '30',
    borderRadius: BORDER_RADIUS.full,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 2,
    borderWidth: 1,
    borderColor: COLORS.accent + '50',
  },
  primaryBadgeText: {
    ...TYPOGRAPHY.captionBold,
    color: COLORS.accent,
  },
  accountNumber: {
    ...TYPOGRAPHY.h4,
    color: COLORS.textOnDark,
    letterSpacing: 2,
    marginBottom: SPACING.md,
    fontWeight: '600',
  },
  balanceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    marginBottom: SPACING.lg,
  },
  balanceLabel: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textOnDarkSub,
    marginBottom: 2,
  },
  balanceAmount: {
    ...TYPOGRAPHY.display,
    color: COLORS.textOnDark,
    fontWeight: '700',
  },
  eyeBtn: {
    padding: SPACING.sm,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: BORDER_RADIUS.full,
  },
  cardActions: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.15)',
    paddingTop: SPACING.md,
  },
  cardActionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.xs,
  },
  cardActionText: {
    ...TYPOGRAPHY.captionBold,
    color: COLORS.textOnDark,
  },
  cardActionDivider: {
    width: 1,
    backgroundColor: 'rgba(255,255,255,0.15)',
    marginVertical: 2,
  },

  // ── Dots ──────────────────────────────────────────────────────────────────
  dotsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: SPACING.md,
    gap: SPACING.xs,
  },
  dot: {
    borderRadius: BORDER_RADIUS.full,
    height: 6,
  },
  dotActive: {
    width: 20,
    backgroundColor: COLORS.accent,
  },
  dotInactive: {
    width: 6,
    backgroundColor: 'rgba(255,255,255,0.35)',
  },

  // ── Content (white area below hero) ───────────────────────────────────────
  content: {
    backgroundColor: COLORS.background,
    borderTopLeftRadius: BORDER_RADIUS.xxxl,
    borderTopRightRadius: BORDER_RADIUS.xxxl,
    marginTop: -BORDER_RADIUS.xl, // Overlap with hero for seamless curve
    paddingTop: SPACING.xl,
  },

  // ── Quick Actions ─────────────────────────────────────────────────────────
  quickActionsSection: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: SPACING.md,
    paddingBottom: SPACING.lg,
  },
  quickAction: {
    alignItems: 'center',
    flex: 1,
  },
  quickActionIcon: {
    width: 52,
    height: 52,
    borderRadius: BORDER_RADIUS.xl,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.xs,
  },
  quickActionLabel: {
    ...TYPOGRAPHY.caption,
    color: COLORS.text,
    fontWeight: '500',
    textAlign: 'center',
  },

  // ── Section ───────────────────────────────────────────────────────────────
  sectionDivider: {
    height: SPACING.xs,
    backgroundColor: COLORS.divider,
  },
  section: {
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.lg,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  sectionTitle: {
    ...TYPOGRAPHY.h4,
    color: COLORS.text,
    fontWeight: '700',
    marginBottom: SPACING.md,
  },
  viewAllText: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.primary,
    marginBottom: SPACING.md,
  },

  // ── Protection Status card ────────────────────────────────────────────────
  protectionCard: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    borderWidth: 1,
    borderColor: COLORS.success + '30',
    ...SHADOWS.small,
  },
  protectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  protectionIconWrap: {
    width: 36,
    height: 36,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.success + '15',
    justifyContent: 'center',
    alignItems: 'center',
  },
  protectionTitle: {
    ...TYPOGRAPHY.bodyMedium,
    color: COLORS.text,
    fontWeight: '600',
  },
  protectionSub: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textSecondary,
    marginTop: 1,
  },
  pulseDotOuter: {
    width: 16,
    height: 16,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.success + '25',
    justifyContent: 'center',
    alignItems: 'center',
  },
  pulseDotInner: {
    width: 8,
    height: 8,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.success,
  },
  signalList: {
    gap: SPACING.sm,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    paddingTop: SPACING.md,
    marginBottom: SPACING.sm,
  },
  signalRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
  },
  signalLabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    flex: 1,
  },
  protectionFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
    marginTop: SPACING.sm,
    paddingTop: SPACING.sm,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  protectionFooterText: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    flex: 1,
  },

  // ── Transaction rows ──────────────────────────────────────────────────────
  txnRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
    gap: SPACING.md,
  },
  txnIcon: {
    width: 42,
    height: 42,
    borderRadius: BORDER_RADIUS.lg,
    justifyContent: 'center',
    alignItems: 'center',
    flexShrink: 0,
  },
  txnDetails: {
    flex: 1,
    minWidth: 0,
  },
  txnName: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.text,
    fontWeight: '600',
    marginBottom: 2,
  },
  txnMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: SPACING.xs,
  },
  txnDate: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
  },
  channelBadge: {
    backgroundColor: COLORS.primaryVeryLight,
    borderRadius: BORDER_RADIUS.full,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 1,
  },
  channelText: {
    ...TYPOGRAPHY.captionBold,
    color: COLORS.primaryMedium,
  },
  blockedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: COLORS.dangerLight,
    borderRadius: BORDER_RADIUS.full,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 1,
  },
  blockedText: {
    ...TYPOGRAPHY.captionBold,
    color: COLORS.danger,
  },
  warnBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: COLORS.cautionLight,
    borderRadius: BORDER_RADIUS.full,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 1,
  },
  warnBadgeText: {
    ...TYPOGRAPHY.captionBold,
    color: COLORS.caution,
  },
  txnAmount: {
    ...TYPOGRAPHY.bodySmMedium,
    fontWeight: '700',
    flexShrink: 0,
  },

  // ── Wealth tip ────────────────────────────────────────────────────────────
  tipCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: COLORS.accentLight,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    borderWidth: 1,
    borderColor: COLORS.accent + '30',
    gap: SPACING.md,
  },
  tipIconWrap: {
    width: 36,
    height: 36,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.accent + '20',
    justifyContent: 'center',
    alignItems: 'center',
    flexShrink: 0,
  },
  tipLabel: {
    ...TYPOGRAPHY.overline,
    color: COLORS.accentDark,
    marginBottom: SPACING.xs,
  },
  tipText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.text,
    lineHeight: 20,
  },
  tipArrow: {
    padding: SPACING.xs,
    alignSelf: 'center',
    flexShrink: 0,
  },
});

export default DashboardScreen;