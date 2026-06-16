// src/screens/WealthOverviewScreen.tsx
// SecureWealth Twin — My Wealth
//
// Strictly scoped to the blueprint's Finals MVP Wealth Intelligence Layer:
//   - Net Worth Analysis        (Assets - Liabilities)
//   - Cash Flow Analysis        (Income / Expenses / Savings)
//   - Goal-Based Recommendations (Emergency Fund, FD, RD, SIP only)
//   - Explainable Recommendations (Why / How sure / Expected benefit)
//
// Explicitly OUT of scope (per blueprint section 8 "Explicitly Out Of Scope"):
//   Stock Picking, Tax Optimization, Mutual Fund Ranking, Insurance Advisory,
//   Credit Card Recommendation Engine, Goal Tracking (house/education/retirement
//   — goal_tracking table is a "Future Expansion Table, Not Finals").
//
// Layout (single scroll, no tabs — consistent with Dashboard's section pattern):
//   1. Hero (green): Net Worth + Assets/Liabilities pills
//   2. Cash Flow card: stacked bar (Income -> Expenses + Savings)
//   3. My Deposits: FD/RD cards with maturity progress
//   4. My Loans: EMI cards with repayment progress
//   5. Smart Recommendations: Emergency Fund / FD / RD / SIP cards
//
// Terminology: "Confidence: 87%" is replaced with a friendly "How sure are we"
// badge (Very likely to help / Likely to help / Worth considering). Banking
// terms (FD, RD, SIP, EMI, Net Worth) keep their names but get a ? info icon
// (placeholder Alert until GlossaryPopup is built in Batch 6).

import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Feather } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import GlossaryPopup from '../components/common/GlossaryPopup';

import accountsData from '../../mockData/accounts.json';
import depositsData from '../../mockData/deposits.json';
import loansData from '../../mockData/loans.json';
import transactionsData from '../../mockData/transactions.json';
import recommendationsData from '../../mockData/recommendations.json';

// ── Helpers ───────────────────────────────────────────────────────────────────
const formatCurrency = (n: number) => '\u20B9' + Math.round(n).toLocaleString('en-IN');

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

// Repayment progress for a loan
const loanProgress = (original: number, outstanding: number): number => {
  if (original <= 0) return 0;
  return Math.min(100, Math.max(0, ((original - outstanding) / original) * 100));
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

// ── Sub-components ────────────────────────────────────────────────────────────

// Deposit card (FD / RD)
const DepositCard = ({ deposit }: { deposit: typeof depositsData[0] }) => {
  const progress = depositProgress(deposit.startDate, deposit.maturityDate);
  const remainingDays = daysUntil(deposit.maturityDate);
  const isFD = deposit.depositType === 'FD';

  return (
    <View style={styles.depositCard}>
      <View style={styles.depositHeader}>
        <View style={styles.depositTypeRow}>
          <View style={[styles.typeChip, { backgroundColor: COLORS.primaryVeryLight }]}>
            <Text style={styles.typeChipText}>{deposit.depositType}</Text>
          </View>
          <GlossaryPopup term={deposit.depositType as any} />
        </View>
        <Text style={styles.depositInstitution}>{deposit.institution}</Text>
      </View>

      <View style={styles.depositValueRow}>
        <View>
          <Text style={styles.depositValueLabel}>Current Value</Text>
          <Text style={styles.depositValue}>{formatCurrency(deposit.currentValue)}</Text>
        </View>
        <View style={styles.depositRateChip}>
          <Text style={styles.depositRateText}>{deposit.interestRate}% p.a.</Text>
        </View>
      </View>

      {/* Maturity progress */}
      <View style={styles.progressTrack}>
        <View style={[styles.progressFill, { width: `${progress}%`, backgroundColor: COLORS.primary }]} />
      </View>
      <View style={styles.depositFooterRow}>
        <Text style={styles.depositFooterText}>
          {isFD
            ? `Started with ${formatCurrency(deposit.principal)}`
            : `${formatCurrency(deposit.monthlyInstallment || 0)}/month`}
        </Text>
        <Text style={styles.depositFooterText}>
          {remainingDays > 0 ? `Matures in ${formatDuration(remainingDays)}` : 'Matured'}
        </Text>
      </View>
    </View>
  );
};

// Loan card
const LoanCard = ({ loan }: { loan: typeof loansData[0] }) => {
  const progress = loanProgress(loan.originalAmount, loan.outstandingAmount);

  return (
    <View style={styles.depositCard}>
      <View style={styles.depositHeader}>
        <View style={styles.depositTypeRow}>
          <View style={[styles.typeChip, { backgroundColor: COLORS.dangerLight }]}>
            <Text style={[styles.typeChipText, { color: COLORS.danger }]}>{loan.loanType} Loan</Text>
          </View>
        </View>
        <Text style={styles.depositInstitution}>{loan.institution}</Text>
      </View>

      <View style={styles.depositValueRow}>
        <View>
          <Text style={styles.depositValueLabel}>Outstanding Amount</Text>
          <Text style={[styles.depositValue, { color: COLORS.text }]}>
            {formatCurrency(loan.outstandingAmount)}
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

      {/* Repayment progress */}
      <View style={styles.progressTrack}>
        <View style={[styles.progressFill, { width: `${progress}%`, backgroundColor: COLORS.success }]} />
      </View>
      <View style={styles.depositFooterRow}>
        <Text style={styles.depositFooterText}>{Math.round(progress)}% paid off</Text>
        <Text style={styles.depositFooterText}>
          {loan.remainingTenureMonths} month{loan.remainingTenureMonths === 1 ? '' : 's'} left
        </Text>
      </View>
    </View>
  );
};

// Recommendation card
const RecommendationCard = ({
  rec,
  expanded,
  onToggle,
}: {
  rec: typeof recommendationsData[0];
  expanded: boolean;
  onToggle: () => void;
}) => {
  const confidence = getConfidenceInfo(rec.confidenceScore);
  const meta = TYPE_META[rec.recommendationType] || { glossaryKey: '', chipLabel: rec.recommendationType };

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
            {meta.glossaryKey ? (
              <GlossaryPopup term={meta.glossaryKey as any} />
            ) : null}
          </View>
        </View>
      </View>

      <Text style={styles.recText}>{rec.recommendationText}</Text>

      {/* How sure are we */}
      <View style={[styles.confidenceBadge, { backgroundColor: confidence.bg }]}>
        <Feather name="compass" size={13} color={confidence.color} />
        <Text style={[styles.confidenceText, { color: confidence.color }]}>{confidence.label}</Text>
      </View>

      {/* Expected benefit — always visible */}
      <View style={styles.benefitRow}>
        <Feather name="gift" size={14} color={COLORS.success} />
        <Text style={styles.benefitText}>{rec.expectedBenefit}</Text>
      </View>

      {/* Why — expandable */}
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
  const [expandedRecId, setExpandedRecId] = useState<string | null>(null);

  // ── Net Worth calculation (data-driven, backend-ready) ──────────────────────
  const totalAccountBalance = accountsData.reduce((sum, a) => sum + a.balance, 0);
  const totalDepositValue = depositsData.reduce((sum, d) => sum + d.currentValue, 0);
  const totalAssets = totalAccountBalance + totalDepositValue;
  const totalLiabilities = loansData.reduce((sum, l) => sum + l.outstandingAmount, 0);
  const netWorth = totalAssets - totalLiabilities;

  // ── Cash flow calculation ────────────────────────────────────────────────────
  // Exclude BLOCKED transactions — money never left the account, so it
  // shouldn't count against (or for) the user's cash flow.
  const nonBlocked = transactionsData.filter((t) => t.decision !== 'BLOCK');
  const income = nonBlocked.filter((t) => t.amount > 0).reduce((sum, t) => sum + t.amount, 0);
  const expenses = nonBlocked
    .filter((t) => t.amount < 0)
    .reduce((sum, t) => sum + Math.abs(t.amount), 0);
  const savings = income - expenses;
  const savingsRate = income > 0 ? Math.round((savings / income) * 100) : 0;

  const expensesPct = income > 0 ? Math.min(100, (expenses / income) * 100) : 0;
  const savingsPct = income > 0 ? Math.max(0, 100 - expensesPct) : 0;

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* ── Hero: Net Worth ── */}
      <View style={styles.hero}>
        <View style={styles.netWorthLabelRow}>
          <Text style={styles.netWorthLabel}>Net Worth</Text>
          <GlossaryPopup term="NET_WORTH">
            <Feather name="help-circle" size={14} color={COLORS.textOnDarkSub} />
          </GlossaryPopup>
        </View>
        <Text style={styles.netWorthValue}>{formatCurrency(netWorth)}</Text>

        <View style={styles.assetLiabilityRow}>
          <View style={styles.assetLiabilityPill}>
            <Feather name="arrow-up-circle" size={14} color={COLORS.textOnDark} />
            <View>
              <Text style={styles.pillLabel}>What you own</Text>
              <Text style={styles.pillValue}>{formatCurrency(totalAssets)}</Text>
            </View>
          </View>
          <View style={styles.assetLiabilityPill}>
            <Feather name="arrow-down-circle" size={14} color={COLORS.textOnDark} />
            <View>
              <Text style={styles.pillLabel}>What you owe</Text>
              <Text style={styles.pillValue}>{formatCurrency(totalLiabilities)}</Text>
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
            {/* Stacked bar: expenses + savings, out of income */}
            <View style={styles.cashFlowBar}>
              <View style={[styles.cashFlowBarSegment, { flex: expensesPct, backgroundColor: COLORS.danger }]} />
              <View style={[styles.cashFlowBarSegment, { flex: savingsPct, backgroundColor: COLORS.accent }]} />
            </View>

            <View style={styles.cashFlowStatsRow}>
              <View style={styles.cashFlowStat}>
                <View style={[styles.cashFlowDot, { backgroundColor: COLORS.success }]} />
                <Text style={styles.cashFlowStatLabel}>Income</Text>
                <Text style={[styles.cashFlowStatValue, { color: COLORS.success }]}>
                  {formatCurrency(income)}
                </Text>
              </View>
              <View style={styles.cashFlowStat}>
                <View style={[styles.cashFlowDot, { backgroundColor: COLORS.danger }]} />
                <Text style={styles.cashFlowStatLabel}>Expenses</Text>
                <Text style={[styles.cashFlowStatValue, { color: COLORS.danger }]}>
                  {formatCurrency(expenses)}
                </Text>
              </View>
              <View style={styles.cashFlowStat}>
                <View style={[styles.cashFlowDot, { backgroundColor: COLORS.accent }]} />
                <Text style={styles.cashFlowStatLabel}>Savings</Text>
                <Text style={[styles.cashFlowStatValue, { color: COLORS.accentDark }]}>
                  {formatCurrency(savings)}
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
          {depositsData.map((deposit) => (
            <DepositCard key={deposit.depositId} deposit={deposit} />
          ))}
        </View>

        <View style={styles.sectionDivider} />

        {/* My Loans */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>My Loans</Text>
          {loansData.map((loan) => (
            <LoanCard key={loan.loanId} loan={loan} />
          ))}
        </View>

        <View style={styles.sectionDivider} />

        {/* Smart Recommendations */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Smart Recommendations</Text>
          <Text style={styles.sectionSubtitle}>
            A few ideas based on your accounts, deposits, and spending
          </Text>

          {recommendationsData.map((rec) => (
            <RecommendationCard
              key={rec.recommendationId}
              rec={rec}
              expanded={expandedRecId === rec.recommendationId}
              onToggle={() =>
                setExpandedRecId((prev) => (prev === rec.recommendationId ? null : rec.recommendationId))
              }
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