// src/screens/WealthOverviewScreen.tsx
// SecureWealth Twin — My Wealth
//
// BACKEND INTEGRATION (was mockData/*.json only) — using the real
// src/api/apiService.ts + src/api/types.ts:
//  • Net Worth      -> api.getNetWorth()              GET /api/v1/aggregation/net-worth
//  • Cash Flow      -> api.getCashflow()               GET /api/v1/aggregation/cashflow
//  • My Deposits    -> api.getDeposits()                GET /api/v1/deposits/
//  • My Loans       -> api.getLoans()                   GET /api/v1/loans/
//  • Smart Recs     -> api.getWealthRecommendations()   POST /api/v1/ai/wealth/recommendations
//                      (profile_data built from accounts/deposits/loans/cashflow
//                       fetched above; fraud_probability defaults to 0.0 since
//                       no live fraud signal feeds this screen)
//
// Scope is unchanged from the mock version — strictly the blueprint's Finals
// MVP Wealth Intelligence Layer (Net Worth, Cash Flow, Deposits, Loans,
// Goal-Based Recommendations for Emergency Fund / FD / RD / SIP only).
//
// TYPE GAPS (flagged, not silently guessed away):
//  • types.ts's DepositResponse has no `current_value` or
//    `monthly_installment` field — only principal/interest_rate/dates. We
//    derive an approximate current value from simple growth over elapsed
//    term, and RDs show the principal as a lump label since there's no
//    monthly-installment field to read. Replace `depositCurrentValue()` with
//    a straight passthrough once/if the backend adds `current_value`.
//  • LoanResponse has no `original_amount` or `institution`. Without an
//    original amount we cannot compute "% paid off", so that progress bar
//    is omitted entirely rather than showing a fake number. Institution is
//    likewise omitted from the loan card header.
//  • WealthRecommendationsResponse.recommendations is typed `unknown[]` in
//    types.ts (backend shape not pinned down yet). normalizeRec() reads a
//    superset of expected field names (snake_case + camelCase) defensively.
//
// Loading / error handling: sections fetch in parallel; a failing
// recommendations call doesn't block Net Worth / Deposits / Loans from
// rendering. Pull-to-refresh re-fetches everything.

import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl, ActivityIndicator } from 'react-native';
import { Feather } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import GlossaryPopup from '../components/common/GlossaryPopup';
import { api, ApiError } from '../api/apiService';
import type {
  DepositResponse,
  LoanResponse,
  NetWorthResponse,
  CashflowResponse,
} from '../api/types';

// ── Helpers ───────────────────────────────────────────────────────────────────
const formatCurrency = (n: number) => '\u20B9' + Math.round(n || 0).toLocaleString('en-IN');

const daysUntil = (dateStr: string): number => {
  const diff = new Date(dateStr).getTime() - Date.now();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
};

const formatDuration = (days: number): string => {
  if (days <= 0) return 'Matured';
  if (days < 60) return `${days} day${days === 1 ? '' : 's'}`;
  const months = Math.round(days / 30);
  return `${months} month${months === 1 ? '' : 's'}`;
};

// Progress from start date to maturity date, clamped 0-100
const depositProgress = (start: string, maturity: string): number => {
  const s = new Date(start).getTime();
  const m = new Date(maturity).getTime();
  const now = Date.now();
  if (m <= s) return 100;
  return Math.min(100, Math.max(0, ((now - s) / (m - s)) * 100));
};

// FALLBACK: DepositResponse has no current_value field. Approximate simple
// growth from principal using elapsed fraction of term and interest_rate.
const depositCurrentValue = (d: DepositResponse): number => {
  const progressFrac = depositProgress(d.start_date, d.maturity_date) / 100;
  return d.principal * (1 + (d.interest_rate / 100) * progressFrac);
};

// Friendly framing for recommendation confidence — replaces "Confidence: 87%"
const getConfidenceInfo = (score: number) => {
  if (score >= 85) {
    return { label: 'Very likely to help you', color: COLORS.success, bg: COLORS.success + '15' };
  }
  if (score >= 70) {
    return { label: 'Likely to help you', color: COLORS.caution, bg: COLORS.cautionLight };
  }
  return { label: 'Worth considering', color: COLORS.info, bg: COLORS.info + '15' };
};

// Recommendation type -> glossary key + chip label
const TYPE_META: Record<string, { glossaryKey: string; chipLabel: string }> = {
  'Emergency Fund': { glossaryKey: 'EMERGENCY_FUND', chipLabel: 'Emergency Fund' },
  FD: { glossaryKey: 'FD', chipLabel: 'FD' },
  RD: { glossaryKey: 'RD', chipLabel: 'RD' },
  SIP: { glossaryKey: 'SIP', chipLabel: 'SIP' },
};

// recommendations is `unknown[]` in types.ts — read defensively across both
// snake_case (documented) and camelCase (in case the serializer differs).
type NormalizedRec = {
  id: string;
  type: string;
  title: string;
  icon: string;
  text: string;
  confidence: number;
  benefit: string;
  reason: string;
};

const normalizeRec = (raw: unknown, index: number): NormalizedRec => {
  const rec = (raw || {}) as Record<string, any>;
  return {
    id: rec.recommendation_id || rec.recommendationId || `${rec.title || 'rec'}-${index}`,
    type: rec.recommendation_type || rec.recommendationType || 'Emergency Fund',
    title: rec.title || 'Recommendation',
    icon: rec.icon || 'gift',
    text: rec.recommendation_text || rec.recommendationText || '',
    confidence: rec.confidence_score ?? rec.confidenceScore ?? 70,
    benefit: rec.expected_benefit || rec.expectedBenefit || '',
    reason: rec.reason || '',
  };
};

// ── Sub-components ────────────────────────────────────────────────────────────

const DepositCard = ({ deposit }: { deposit: DepositResponse }) => {
  const currentValue = depositCurrentValue(deposit);
  const progress = depositProgress(deposit.start_date, deposit.maturity_date);
  const remainingDays = daysUntil(deposit.maturity_date);
  const isFD = deposit.deposit_type === 'FD';

  return (
    <View style={styles.depositCard}>
      <View style={styles.depositHeader}>
        <View style={styles.depositTypeRow}>
          <View style={[styles.typeChip, { backgroundColor: COLORS.primaryVeryLight }]}>
            <Text style={styles.typeChipText}>{deposit.deposit_type}</Text>
          </View>
          <GlossaryPopup term={deposit.deposit_type as any} />
        </View>
        <Text style={styles.depositInstitution}>{deposit.institution}</Text>
      </View>

      <View style={styles.depositValueRow}>
        <View>
          <Text style={styles.depositValueLabel}>Current Value (est.)</Text>
          <Text style={styles.depositValue}>{formatCurrency(currentValue)}</Text>
        </View>
        <View style={styles.depositRateChip}>
          <Text style={styles.depositRateText}>{deposit.interest_rate}% p.a.</Text>
        </View>
      </View>

      <View style={styles.progressTrack}>
        <View style={[styles.progressFill, { width: `${progress}%`, backgroundColor: COLORS.primary }]} />
      </View>
      <View style={styles.depositFooterRow}>
        <Text style={styles.depositFooterText}>
          {isFD ? `Started with ${formatCurrency(deposit.principal)}` : `Principal ${formatCurrency(deposit.principal)}`}
        </Text>
        <Text style={styles.depositFooterText}>
          {remainingDays > 0 ? `Matures in ${formatDuration(remainingDays)}` : 'Matured'}
        </Text>
      </View>
    </View>
  );
};

const LoanCard = ({ loan }: { loan: LoanResponse }) => {
  return (
    <View style={styles.depositCard}>
      <View style={styles.depositHeader}>
        <View style={styles.depositTypeRow}>
          <View style={[styles.typeChip, { backgroundColor: COLORS.dangerLight }]}>
            <Text style={[styles.typeChipText, { color: COLORS.danger }]}>{loan.loan_type} Loan</Text>
          </View>
        </View>
      </View>

      <View style={styles.depositValueRow}>
        <View>
          <Text style={styles.depositValueLabel}>Outstanding Amount</Text>
          <Text style={[styles.depositValue, { color: COLORS.text }]}>
            {formatCurrency(loan.outstanding_amount)}
          </Text>
        </View>
        <View style={styles.emiChip}>
          <GlossaryPopup term="EMI">
            <View style={styles.emiChipTouchable}>
              <Text style={styles.emiChipText}>{formatCurrency(loan.emi)}/mo EMI</Text>
              <Feather name="help-circle" size={12} color={COLORS.textTertiary} />
            </View>
          </GlossaryPopup>
        </View>
      </View>

      {/* No original_amount from backend -> no "% paid off" progress bar (see header note) */}
      <View style={styles.depositFooterRow}>
        <Text style={styles.depositFooterText}>{loan.interest_rate}% interest</Text>
        <Text style={styles.depositFooterText}>
          {loan.remaining_tenure} month{loan.remaining_tenure === 1 ? '' : 's'} left
        </Text>
      </View>
    </View>
  );
};

const RecommendationCard = ({
  rec,
  expanded,
  onToggle,
}: {
  rec: NormalizedRec;
  expanded: boolean;
  onToggle: () => void;
}) => {
  const confidence = getConfidenceInfo(rec.confidence);
  const meta = TYPE_META[rec.type] || { glossaryKey: '', chipLabel: rec.type };

  return (
    <View style={styles.recCard}>
      <View style={styles.recHeader}>
        <View style={styles.recIconWrap}>
          <Feather name={rec.icon as any} size={20} color={COLORS.accent} />
        </View>
        <View style={styles.recHeaderText}>
          <Text style={styles.recTitle}>{rec.title}</Text>
          <View style={styles.recTypeRow}>
            <View style={styles.recTypeChip}>
              <Text style={styles.recTypeChipText}>{meta.chipLabel}</Text>
            </View>
            {meta.glossaryKey ? <GlossaryPopup term={meta.glossaryKey as any} /> : null}
          </View>
        </View>
      </View>

      <Text style={styles.recText}>{rec.text}</Text>

      <View style={[styles.confidenceBadge, { backgroundColor: confidence.bg }]}>
        <Feather name="compass" size={13} color={confidence.color} />
        <Text style={[styles.confidenceText, { color: confidence.color }]}>{confidence.label}</Text>
      </View>

      <View style={styles.benefitRow}>
        <Feather name="gift" size={14} color={COLORS.success} />
        <Text style={styles.benefitText}>{rec.benefit}</Text>
      </View>

      <TouchableOpacity style={styles.whyRow} onPress={onToggle} activeOpacity={0.7}>
        <Text style={styles.whyLabel}>Why are we suggesting this?</Text>
        <Feather name={expanded ? 'chevron-up' : 'chevron-down'} size={16} color={COLORS.textTertiary} />
      </TouchableOpacity>
      {expanded && <Text style={styles.whyText}>{rec.reason}</Text>}
    </View>
  );
};

// ── Main Screen ───────────────────────────────────────────────────────────────
const WealthOverviewScreen = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [deposits, setDeposits] = useState<DepositResponse[]>([]);
  const [loans, setLoans] = useState<LoanResponse[]>([]);
  const [netWorth, setNetWorth] = useState<NetWorthResponse | null>(null);
  const [cashflow, setCashflow] = useState<CashflowResponse | null>(null);
  const [recommendations, setRecommendations] = useState<NormalizedRec[]>([]);
  const [recsError, setRecsError] = useState(false);
  const [suppressedNote, setSuppressedNote] = useState<string | null>(null);

  const [expandedRecId, setExpandedRecId] = useState<string | null>(null);

  const loadAll = useCallback(async () => {
    setError(null);
    setRecsError(false);
    setSuppressedNote(null);
    try {
      const [accountsRes, depositsRes, loansRes, netWorthRes, cashflowRes] = await Promise.all([
        api.getAccounts(),
        api.getDeposits(),
        api.getLoans(),
        api.getNetWorth(),
        api.getCashflow(),
      ]);
      setDeposits(depositsRes);
      setLoans(loansRes);
      setNetWorth(netWorthRes);
      setCashflow(cashflowRes);

      // Recommendations depend on the profile built from the above — fetch
      // separately so a failure here doesn't blank the rest of the screen.
      try {
        const profileData: Record<string, unknown> = {
          accounts: accountsRes,
          deposits: depositsRes,
          loans: loansRes,
          net_worth: netWorthRes,
          cashflow: cashflowRes,
        };
        const recRes = await api.getWealthRecommendations({
          profile_data: profileData,
          fraud_probability: 0.0,
        });
        if (recRes.suppressed) {
          setSuppressedNote(recRes.disclaimer || 'Recommendations are paused for your account right now.');
          setRecommendations([]);
        } else {
          setRecommendations((recRes.recommendations || []).map(normalizeRec));
        }
      } catch {
        setRecsError(true);
        setRecommendations([]);
      }
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? e.isNetworkError
            ? 'Cannot reach the server. Check your connection and try again.'
            : e.message
          : 'Could not load your wealth data. Pull down to try again.';
      setError(msg);
    }
  }, []);

  useEffect(() => {
    (async () => {
      setLoading(true);
      await loadAll();
      setLoading(false);
    })();
  }, [loadAll]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadAll();
    setRefreshing(false);
  };

  const savingsRate =
    cashflow && cashflow.total_income > 0
      ? Math.round((cashflow.net_cashflow / cashflow.total_income) * 100)
      : 0;
  const expensesPct =
    cashflow && cashflow.total_income > 0
      ? Math.min(100, (cashflow.total_expenses / cashflow.total_income) * 100)
      : 0;
  const savingsPct = cashflow && cashflow.total_income > 0 ? Math.max(0, 100 - expensesPct) : 0;

  if (loading) {
    return (
      <View style={styles.loadingRoot}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Loading your wealth overview…</Text>
      </View>
    );
  }

  if (error && !netWorth) {
    return (
      <View style={styles.loadingRoot}>
        <Feather name="alert-triangle" size={28} color={COLORS.danger} />
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity
          style={styles.retryBtn}
          onPress={async () => {
            setLoading(true);
            await loadAll();
            setLoading(false);
          }}
          activeOpacity={0.8}
        >
          <Text style={styles.retryBtnText}>Try Again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} tintColor={COLORS.textOnDark} />
      }
    >
      {/* ── Hero: Net Worth ── */}
      <View style={styles.hero}>
        <View style={styles.netWorthLabelRow}>
          <Text style={styles.netWorthLabel}>Net Worth</Text>
          <GlossaryPopup term="NET_WORTH">
            <Feather name="help-circle" size={14} color={COLORS.textOnDarkSub} />
          </GlossaryPopup>
        </View>
        <Text style={styles.netWorthValue}>{formatCurrency(netWorth?.net_worth || 0)}</Text>

        <View style={styles.assetLiabilityRow}>
          <View style={styles.assetLiabilityPill}>
            <Feather name="arrow-up-circle" size={14} color={COLORS.textOnDark} />
            <View>
              <Text style={styles.pillLabel}>What you own</Text>
              <Text style={styles.pillValue}>{formatCurrency(netWorth?.total_assets || 0)}</Text>
            </View>
          </View>
          <View style={styles.assetLiabilityPill}>
            <Feather name="arrow-down-circle" size={14} color={COLORS.textOnDark} />
            <View>
              <Text style={styles.pillLabel}>What you owe</Text>
              <Text style={styles.pillValue}>{formatCurrency(netWorth?.total_liabilities || 0)}</Text>
            </View>
          </View>
        </View>
      </View>

      {/* ── Content ── */}
      <View style={styles.content}>
        {/* Cash Flow */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>This Month's Cash Flow</Text>

          <View style={styles.cashFlowCard}>
            <View style={styles.cashFlowBar}>
              <View style={[styles.cashFlowBarSegment, { flex: expensesPct, backgroundColor: COLORS.danger }]} />
              <View style={[styles.cashFlowBarSegment, { flex: savingsPct, backgroundColor: COLORS.accent }]} />
            </View>

            <View style={styles.cashFlowStatsRow}>
              <View style={styles.cashFlowStat}>
                <View style={[styles.cashFlowDot, { backgroundColor: COLORS.success }]} />
                <Text style={styles.cashFlowStatLabel}>Income</Text>
                <Text style={[styles.cashFlowStatValue, { color: COLORS.success }]}>
                  {formatCurrency(cashflow?.total_income || 0)}
                </Text>
              </View>
              <View style={styles.cashFlowStat}>
                <View style={[styles.cashFlowDot, { backgroundColor: COLORS.danger }]} />
                <Text style={styles.cashFlowStatLabel}>Expenses</Text>
                <Text style={[styles.cashFlowStatValue, { color: COLORS.danger }]}>
                  {formatCurrency(cashflow?.total_expenses || 0)}
                </Text>
              </View>
              <View style={styles.cashFlowStat}>
                <View style={[styles.cashFlowDot, { backgroundColor: COLORS.accent }]} />
                <Text style={styles.cashFlowStatLabel}>Savings</Text>
                <Text style={[styles.cashFlowStatValue, { color: COLORS.accentDark }]}>
                  {formatCurrency(cashflow?.net_cashflow || 0)}
                </Text>
              </View>
            </View>

            <View style={styles.savingsRateNote}>
              <Feather name="trending-up" size={14} color={COLORS.primary} />
              <Text style={styles.savingsRateText}>
                You saved about {savingsRate}% of what you earned this month — nice work!
              </Text>
            </View>
          </View>
        </View>

        <View style={styles.sectionDivider} />

        {/* My Deposits */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>My Deposits</Text>
          {deposits.length === 0 ? (
            <Text style={styles.emptyText}>No deposits linked yet.</Text>
          ) : (
            deposits.map((deposit) => <DepositCard key={deposit.deposit_id} deposit={deposit} />)
          )}
        </View>

        <View style={styles.sectionDivider} />

        {/* My Loans */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>My Loans</Text>
          {loans.length === 0 ? (
            <Text style={styles.emptyText}>No loans linked — nothing owed here.</Text>
          ) : (
            loans.map((loan) => <LoanCard key={loan.loan_id} loan={loan} />)
          )}
        </View>

        <View style={styles.sectionDivider} />

        {/* Smart Recommendations */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Smart Recommendations</Text>
          <Text style={styles.sectionSubtitle}>
            A few ideas based on your accounts, deposits, and spending
          </Text>

          {suppressedNote && <Text style={styles.emptyText}>{suppressedNote}</Text>}
          {recsError && (
            <Text style={styles.emptyText}>
              We couldn't load personalized recommendations right now. Pull down to refresh.
            </Text>
          )}
          {!suppressedNote && !recsError && recommendations.length === 0 && (
            <Text style={styles.emptyText}>No recommendations yet — check back after a bit more activity.</Text>
          )}

          {recommendations.map((rec) => (
            <RecommendationCard
              key={rec.id}
              rec={rec}
              expanded={expandedRecId === rec.id}
              onToggle={() => setExpandedRecId((prev) => (prev === rec.id ? null : rec.id))}
            />
          ))}
        </View>

        <View style={{ height: SPACING.xxl }} />
      </View>
    </ScrollView>
  );
};

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.primaryDark,
  },
  loadingRoot: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.background,
    padding: SPACING.lg,
    gap: SPACING.sm,
  },
  loadingText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
  },
  errorText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    textAlign: 'center',
  },
  retryBtn: {
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.lg,
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.sm,
    marginTop: SPACING.sm,
  },
  retryBtnText: {
    ...TYPOGRAPHY.button,
    color: COLORS.textOnDark,
  },
  emptyText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textTertiary,
    marginTop: SPACING.sm,
  },

  // Hero
  hero: {
    backgroundColor: COLORS.primaryDark,
    paddingHorizontal: SPACING.lg,
    paddingTop: SPACING.md,
    paddingBottom: SPACING.xl,
  },
  netWorthLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
    marginBottom: SPACING.xs,
  },
  netWorthLabel: {
    ...TYPOGRAPHY.label,
    color: COLORS.textOnDarkSub,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  netWorthValue: {
    ...TYPOGRAPHY.display,
    color: COLORS.accent,
    fontWeight: '700',
    marginBottom: SPACING.lg,
  },
  assetLiabilityRow: {
    flexDirection: 'row',
    gap: SPACING.md,
  },
  assetLiabilityPill: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
  },
  pillLabel: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textOnDarkSub,
  },
  pillValue: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.textOnDark,
    fontWeight: '700',
    marginTop: 1,
  },

  // Content
  content: {
    backgroundColor: COLORS.background,
    borderTopLeftRadius: BORDER_RADIUS.xxxl,
    borderTopRightRadius: BORDER_RADIUS.xxxl,
    marginTop: -BORDER_RADIUS.xl,
    paddingTop: SPACING.xl,
  },
  sectionDivider: {
    height: SPACING.xs,
    backgroundColor: COLORS.divider,
  },
  section: {
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.lg,
  },
  sectionTitle: {
    ...TYPOGRAPHY.h4,
    color: COLORS.text,
    fontWeight: '700',
    marginBottom: SPACING.xs,
  },
  sectionSubtitle: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginBottom: SPACING.md,
  },

  // Cash flow
  cashFlowCard: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    marginTop: SPACING.sm,
    ...SHADOWS.small,
  },
  cashFlowBar: {
    flexDirection: 'row',
    height: 10,
    borderRadius: BORDER_RADIUS.full,
    overflow: 'hidden',
    backgroundColor: COLORS.divider,
    marginBottom: SPACING.md,
  },
  cashFlowBarSegment: {
    height: '100%',
  },
  cashFlowStatsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: SPACING.md,
  },
  cashFlowStat: {
    flex: 1,
  },
  cashFlowDot: {
    width: 8,
    height: 8,
    borderRadius: BORDER_RADIUS.full,
    marginBottom: SPACING.xs,
  },
  cashFlowStatLabel: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
  },
  cashFlowStatValue: {
    ...TYPOGRAPHY.bodySmMedium,
    fontWeight: '700',
    marginTop: 1,
  },
  savingsRateNote: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: SPACING.sm,
    borderTopWidth: 1,
    borderTopColor: COLORS.divider,
    paddingTop: SPACING.md,
  },
  savingsRateText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    flex: 1,
    lineHeight: 19,
  },

  // Deposit / Loan card (shared layout)
  depositCard: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    marginTop: SPACING.sm,
    ...SHADOWS.small,
  },
  depositHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  depositTypeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
  },
  typeChip: {
    borderRadius: BORDER_RADIUS.full,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 3,
  },
  typeChipText: {
    ...TYPOGRAPHY.captionBold,
    color: COLORS.primaryMedium,
  },
  depositInstitution: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
  },
  depositValueRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    marginBottom: SPACING.md,
  },
  depositValueLabel: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    marginBottom: 2,
  },
  depositValue: {
    ...TYPOGRAPHY.h3,
    color: COLORS.primary,
    fontWeight: '700',
  },
  depositRateChip: {
    backgroundColor: COLORS.accentLight,
    borderRadius: BORDER_RADIUS.full,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 3,
  },
  depositRateText: {
    ...TYPOGRAPHY.captionBold,
    color: COLORS.accentDark,
  },
  emiChip: {
    alignItems: 'flex-end',
  },
  emiChipTouchable: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: COLORS.surfaceLight,
    borderRadius: BORDER_RADIUS.full,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 3,
  },
  emiChipText: {
    ...TYPOGRAPHY.captionBold,
    color: COLORS.textSecondary,
  },
  progressTrack: {
    height: 6,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.divider,
    overflow: 'hidden',
    marginBottom: SPACING.sm,
  },
  progressFill: {
    height: '100%',
    borderRadius: BORDER_RADIUS.full,
  },
  depositFooterRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  depositFooterText: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
  },

  // Recommendation card
  recCard: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    marginTop: SPACING.sm,
    ...SHADOWS.small,
  },
  recHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: SPACING.md,
    marginBottom: SPACING.sm,
  },
  recIconWrap: {
    width: 40,
    height: 40,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.accentLight,
    justifyContent: 'center',
    alignItems: 'center',
    flexShrink: 0,
  },
  recHeaderText: {
    flex: 1,
  },
  recTitle: {
    ...TYPOGRAPHY.bodyMedium,
    color: COLORS.text,
    fontWeight: '700',
    marginBottom: 4,
  },
  recTypeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
  },
  recTypeChip: {
    backgroundColor: COLORS.primaryVeryLight,
    borderRadius: BORDER_RADIUS.full,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 2,
  },
  recTypeChipText: {
    ...TYPOGRAPHY.captionBold,
    color: COLORS.primaryMedium,
  },
  recText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    lineHeight: 20,
    marginBottom: SPACING.md,
  },
  confidenceBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
    alignSelf: 'flex-start',
    borderRadius: BORDER_RADIUS.full,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 4,
    marginBottom: SPACING.sm,
  },
  confidenceText: {
    ...TYPOGRAPHY.captionBold,
  },
  benefitRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: SPACING.sm,
    marginBottom: SPACING.sm,
  },
  benefitText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.text,
    flex: 1,
    lineHeight: 19,
  },
  whyRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: COLORS.divider,
    paddingTop: SPACING.sm,
  },
  whyLabel: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.primary,
  },
  whyText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginTop: SPACING.sm,
    lineHeight: 19,
  },
});

export default WealthOverviewScreen;