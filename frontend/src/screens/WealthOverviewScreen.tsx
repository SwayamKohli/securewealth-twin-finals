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

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl, ActivityIndicator } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useFocusEffect } from '@react-navigation/native';

import { COLORS } from '../constants/colors';
import { useI18n } from '../i18n';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import GlossaryPopup from '../components/common/GlossaryPopup';
import LinkedBanksCard from '../components/LinkedBanksCard';
import { WealthSkeleton } from '../components/common/Skeleton';
import ConsentScreen from './ConsentScreen';
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

// The wealth engine emits: recommendation_id, recommendation (title), product,
// amount, tenure, reason, confidence (0-1), expected_benefit, priority, source.
// The previous reader looked for title/recommendation_text/confidence_score —
// none of which exist — so every card rendered as "Recommendation" with a
// hardcoded 70% confidence. Read the real keys, keep the old ones as fallbacks.
type NormalizedRec = {
  id: string;
  title: string;
  product: string;
  amount: number;
  tenure: string;
  priority: string;
  icon: string;
  confidence: number;   // 0-100
  benefit: string;
  reason: string;
  source: string;
};

// Product string -> icon + the glossary term to explain it.
const PRODUCT_META: { match: RegExp; icon: string; glossary: string; category?: string }[] = [
  { match: /liquid/i,     icon: 'droplet',    glossary: 'FD',  category: 'LIQUID_MUTUAL_FUND' },
  { match: /elss|tax/i,   icon: 'percent',    glossary: 'SIP', category: 'ELSS_MUTUAL_FUND' },
  { match: /sip|equity/i, icon: 'trending-up', glossary: 'SIP', category: 'EQUITY_MUTUAL_FUND' },
  { match: /recurring|rd/i, icon: 'repeat',   glossary: 'RD' },
  { match: /fixed deposit|fd/i, icon: 'lock', glossary: 'FD' },
  { match: /debt|loan|prepay/i, icon: 'trending-down', glossary: '' },
  { match: /budget|expense/i, icon: 'pie-chart', glossary: '' },
];

const productMeta = (product: string) =>
  PRODUCT_META.find((m) => m.match.test(product || '')) || {
    icon: 'gift',
    glossary: '',
    category: undefined as string | undefined,
  };

// Confidence arrives as 0-1 from the engine; older payloads used 0-100.
const toPercent = (value: unknown): number => {
  const n = Number(value);
  if (!Number.isFinite(n)) return 70;
  return n <= 1 ? Math.round(n * 100) : Math.round(n);
};

const normalizeRec = (raw: unknown, index: number): NormalizedRec => {
  const rec = (raw || {}) as Record<string, any>;
  return {
    id: rec.recommendation_id || rec.recommendationId || `rec-${index}`,
    title: rec.recommendation || rec.title || 'Recommendation',
    product: rec.product || '',
    amount: Number(rec.amount) || 0,
    tenure: rec.tenure || '',
    priority: String(rec.priority || '').toLowerCase(),
    icon: productMeta(rec.product || '').icon,
    confidence: toPercent(rec.confidence ?? rec.confidence_score ?? rec.confidenceScore),
    benefit: rec.expected_benefit || rec.expectedBenefit || '',
    reason: rec.reason || '',
    source: rec.source || '',
  };
};

const PRIORITY_META: Record<string, { label: string; color: string; bg: string }> = {
  high: { label: 'Do this first', color: '#B45309', bg: '#FEF3C7' },
  medium: { label: 'Worth doing', color: '#1D4ED8', bg: '#DBEAFE' },
  low: { label: 'When you can', color: '#15803D', bg: '#DCFCE7' },
};

const GRADE_META: Record<string, { label: string; color: string }> = {
  A: { label: 'Strong', color: '#15803D' },
  B: { label: 'Healthy', color: '#65A30D' },
  C: { label: 'Needs attention', color: '#B45309' },
  D: { label: 'At risk', color: '#DC2626' },
};

const COMPONENT_LABELS: Record<string, string> = {
  emergency_readiness: 'Emergency readiness',
  debt_management: 'Debt management',
  savings_discipline: 'Savings discipline',
  wealth_buffer: 'Wealth buffer',
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
  const { t } = useI18n();
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
          <Text style={styles.depositValueLabel}>{t('wealth.outstanding')}</Text>
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
  liveReason,
  loadingReason,
  onStart,
}: {
  rec: NormalizedRec;
  expanded: boolean;
  onToggle: () => void;
  liveReason?: string;
  loadingReason?: boolean;
  onStart: (rec: NormalizedRec) => void;
}) => {
  const { t } = useI18n();
  const confidence = getConfidenceInfo(rec.confidence);
  const meta = productMeta(rec.product);
  const priority = PRIORITY_META[rec.priority];
  // Only offer "Start this" for products the Invest screen can actually open.
  const actionable = !!meta.category && rec.amount > 0;

  return (
    <View style={styles.recCard}>
      <View style={styles.recHeader}>
        <View style={styles.recIconWrap}>
          <Feather name={rec.icon as any} size={20} color={COLORS.accent} />
        </View>
        <View style={styles.recHeaderText}>
          <Text style={styles.recTitle}>{rec.title}</Text>
          <View style={styles.recTypeRow}>
            {rec.product ? (
              <View style={styles.recTypeChip}>
                <Text style={styles.recTypeChipText}>{rec.product}</Text>
              </View>
            ) : null}
            {meta.glossary ? <GlossaryPopup term={meta.glossary as any} /> : null}
          </View>
        </View>
        {priority ? (
          <View style={[styles.priorityChip, { backgroundColor: priority.bg }]}>
            <Text style={[styles.priorityChipText, { color: priority.color }]}>
              {priority.label}
            </Text>
          </View>
        ) : null}
      </View>

      {/* The two numbers that actually drive a decision */}
      {(rec.amount > 0 || rec.tenure) && (
        <View style={styles.recFactRow}>
          {rec.amount > 0 && (
            <View style={styles.recFact}>
              <Text style={styles.recFactLabel}>{t('wealth.suggestedAmount')}</Text>
              <Text style={styles.recFactValue}>{formatCurrency(rec.amount)}</Text>
            </View>
          )}
          {rec.tenure ? (
            <View style={styles.recFact}>
              <Text style={styles.recFactLabel}>Tenure</Text>
              <Text style={styles.recFactValue}>{rec.tenure}</Text>
            </View>
          ) : null}
        </View>
      )}

      {rec.benefit ? (
        <View style={styles.benefitRow}>
          <Feather name="gift" size={14} color={COLORS.success} />
          <Text style={styles.benefitText}>{rec.benefit}</Text>
        </View>
      ) : null}

      {/* Confidence as a bar, not a bare percentage */}
      <View style={styles.confidenceBlock}>
        <View style={styles.confidenceLabelRow}>
          <Feather name="compass" size={13} color={confidence.color} />
          <Text style={[styles.confidenceText, { color: confidence.color }]}>
            {confidence.label}
          </Text>
        </View>
        <View style={styles.confidenceTrack}>
          <View
            style={[
              styles.confidenceFill,
              { width: `${Math.min(100, Math.max(6, rec.confidence))}%`, backgroundColor: confidence.color },
            ]}
          />
        </View>
      </View>

      <TouchableOpacity style={styles.whyRow} onPress={onToggle} activeOpacity={0.7}>
        <Text style={styles.whyLabel}>{t('wealth.whyThis')}</Text>
        <Feather
          name={expanded ? 'chevron-up' : 'chevron-down'}
          size={16}
          color={COLORS.textTertiary}
        />
      </TouchableOpacity>
      {expanded && (
        <View>
          {loadingReason ? (
            <ActivityIndicator
              size="small"
              color={COLORS.primary}
              style={{ alignSelf: 'flex-start', marginTop: SPACING.sm }}
            />
          ) : (
            <Text style={styles.whyText}>{liveReason || rec.reason}</Text>
          )}
          {rec.source ? <Text style={styles.recSource}>Basis: {rec.source}</Text> : null}
        </View>
      )}

      {actionable && (
        <TouchableOpacity
          style={styles.startBtn}
          onPress={() => onStart(rec)}
          activeOpacity={0.85}
        >
          <Feather name="arrow-right-circle" size={15} color={COLORS.textOnDark} />
          <Text style={styles.startBtnText}>Start this — {formatCurrency(rec.amount)}</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

// Financial health: the score, its grade, and WHICH component is dragging it
// down. A bare number tells the customer nothing they can act on.
const HealthCard = ({ health }: { health: Record<string, any> | null }) => {
  const { t } = useI18n();
  if (!health || typeof health.score !== 'number') return null;
  const grade = String(health.grade || '').toUpperCase();
  const meta = GRADE_META[grade] || { label: '', color: COLORS.primary };
  const components = (health.components || {}) as Record<string, number>;

  return (
    <View style={styles.healthCard}>
      <View style={styles.healthHead}>
        <View>
          <Text style={styles.healthLabel}>{t('wealth.health')}</Text>
          <Text style={styles.healthSub}>{meta.label}</Text>
        </View>
        <View style={[styles.gradeBadge, { borderColor: meta.color }]}>
          <Text style={[styles.gradeText, { color: meta.color }]}>{grade}</Text>
          <Text style={styles.gradeScore}>{Math.round(health.score)}/100</Text>
        </View>
      </View>

      {Object.entries(components).map(([key, value]) => {
        const pct = Math.max(0, Math.min(100, (Number(value) / 25) * 100));
        return (
          <View key={key} style={styles.componentRow}>
            <Text style={styles.componentLabel}>{COMPONENT_LABELS[key] || key}</Text>
            <View style={styles.componentTrack}>
              <View
                style={[
                  styles.componentFill,
                  {
                    width: `${pct}%`,
                    backgroundColor: pct >= 75 ? COLORS.success : pct >= 40 ? COLORS.caution : COLORS.danger,
                  },
                ]}
              />
            </View>
            <Text style={styles.componentValue}>{Math.round(Number(value))}/25</Text>
          </View>
        );
      })}
      <Text style={styles.healthNote}>
        Each part is scored out of 25. The lowest bar is the fastest thing to improve.
      </Text>
    </View>
  );
};

// ── Main Screen ───────────────────────────────────────────────────────────────
const WealthOverviewScreen = ({ navigation }: any) => {
  const { t } = useI18n();
  const [loading, setLoading] = useState(true);
  // Task 2.1 — aggregated endpoints sit behind `require_aa_consent`. null =
  // not yet known, false = show the consent gate instead of an error.
  const [hasConsent, setHasConsent] = useState<boolean | null>(null);
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

  // Task 4.9 — live explanations from /ai/explainability/wealth, keyed by
  // recommendation_id. The engine's own `reason` is the fallback, so an
  // unreachable explainability service degrades to plain text, never to blank.
  const [health, setHealth] = useState<Record<string, any> | null>(null);
  const [liveReasons, setLiveReasons] = useState<Record<string, string>>({});
  const [reasonsLoading, setReasonsLoading] = useState(false);

  const loadAll = useCallback(async () => {
    setError(null);
    setRecsError(false);
    setSuppressedNote(null);
    setLiveReasons({});

    // Consent first: without it every aggregated call below returns 403, and
    // showing the customer a raw error is worse than showing them the choice.
    try {
      const consent = await api.getConsent();
      setHasConsent(consent.aa_consent);
      if (!consent.aa_consent) return;
    } catch {
      // Consent endpoint unreachable — carry on and let the calls below decide.
      setHasConsent(true);
    }

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
        setHealth((recRes.financial_health as Record<string, any>) || null);

        // Explanations are a nice-to-have: fetch them without blocking the
        // cards, and swallow failures.
        setReasonsLoading(true);
        api
          .explainWealth({
            wealth_result: recRes as unknown as Record<string, unknown>,
            profile: profileData,
          })
          .then((exp) => {
            const map: Record<string, string> = {};
            for (const item of exp.recommendation_explanations || []) {
              const entry = item as Record<string, any>;
              if (entry.recommendation_id && entry.explanation) {
                map[entry.recommendation_id] = entry.explanation;
              }
            }
            setLiveReasons(map);
          })
          .catch(() => setLiveReasons({}))
          .finally(() => setReasonsLoading(false));

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
      // A 403 here means consent was withdrawn between checks — gate, don't error.
      if (e instanceof ApiError && e.status === 403) {
        setHasConsent(false);
        return;
      }
      const msg =
        e instanceof ApiError
          ? e.isConnectivityError
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

  // Refresh whenever the tab regains focus.
  //
  // This previously only re-checked consent, so coming back from a completed
  // investment showed the OLD balance until the customer pulled to refresh —
  // it looked as though the money had not moved. Skips the very first focus,
  // because the initial load has already just run.
  const firstFocus = useRef(true);
  useFocusEffect(
    useCallback(() => {
      let active = true;

      api
        .getConsent()
        .then((c) => {
          if (active) setHasConsent(c.aa_consent);
        })
        .catch(() => undefined);

      if (firstFocus.current) {
        firstFocus.current = false;
      } else {
        // Silent: no skeleton, no spinner. The screen already has data; it is
        // being brought up to date, not loaded from nothing.
        loadAll();
      }

      return () => {
        active = false;
      };
    }, [loadAll])
  );

  // Task 4.11 — close the loop between advice and action. This only pre-fills
  // the Invest screen; the customer still confirms and the full security
  // pipeline still runs on the resulting investment.
  const startFromRecommendation = (rec: NormalizedRec) => {
    const meta = productMeta(rec.product);
    navigation?.navigate('TransactionInitiate', {
      prefill: {
        amount: rec.amount,
        fundCategory: meta.category,
        source: rec.id,
      },
    });
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadAll();
    setRefreshing(false);
  };

  const assetsTotal = netWorth?.total_assets || 0;
  const liabilitiesTotal = netWorth?.total_liabilities || 0;

  const savingsRate =
    cashflow && cashflow.total_income > 0
      ? Math.round((cashflow.net_cashflow / cashflow.total_income) * 100)
      : 0;
  const expensesPct =
    cashflow && cashflow.total_income > 0
      ? Math.min(100, (cashflow.total_expenses / cashflow.total_income) * 100)
      : 0;
  const savingsPct = cashflow && cashflow.total_income > 0 ? Math.max(0, 100 - expensesPct) : 0;

  // Skeleton rather than a spinner: this tab opens on a net-worth figure, and
  // a blank screen followed by a sudden number reads as instability.
  if (loading) return <WealthSkeleton />;

  // Consent gate — replaces the whole tab until the customer decides.
  if (hasConsent === false) {
    return (
      <ConsentScreen
        onGranted={async () => {
          setLoading(true);
          setHasConsent(true);
          await loadAll();
          setLoading(false);
        }}
      />
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
          <Text style={styles.retryBtnText}>{t('common.tryAgain')}</Text>
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
          <Text style={styles.netWorthLabel}>{t('common.netWorth')}</Text>
          <GlossaryPopup term="NET_WORTH">
            <Feather name="help-circle" size={14} color={COLORS.textOnDarkSub} />
          </GlossaryPopup>
        </View>
        <Text style={styles.netWorthValue}>{formatCurrency(netWorth?.net_worth || 0)}</Text>

        <View style={styles.assetLiabilityRow}>
          <View style={styles.assetLiabilityPill}>
            <Feather name="arrow-up-circle" size={14} color={COLORS.textOnDark} />
            <View>
              <Text style={styles.pillLabel}>{t('wealth.whatYouOwn')}</Text>
              <Text style={styles.pillValue}>{formatCurrency(netWorth?.total_assets || 0)}</Text>
            </View>
          </View>
          <View style={styles.assetLiabilityPill}>
            <Feather name="arrow-down-circle" size={14} color={COLORS.textOnDark} />
            <View>
              <Text style={styles.pillLabel}>{t('wealth.whatYouOwe')}</Text>
              <Text style={styles.pillValue}>{formatCurrency(netWorth?.total_liabilities || 0)}</Text>
            </View>
          </View>
        </View>

        {/* Task 4.10 — the two numbers to scale. Seeing that what you owe is
            a thin sliver (or isn't) lands faster than reading both figures. */}
        {assetsTotal + liabilitiesTotal > 0 && (
          <View style={styles.nwBarWrap}>
            <View style={styles.nwBar}>
              <View style={[styles.nwBarAsset, { flex: Math.max(assetsTotal, 0.0001) }]} />
              <View style={[styles.nwBarLiability, { flex: Math.max(liabilitiesTotal, 0.0001) }]} />
            </View>
            <Text style={styles.nwBarCaption}>
              {liabilitiesTotal === 0
                ? 'You have no borrowings against these assets.'
                : `What you owe is ${Math.round((liabilitiesTotal / (assetsTotal + liabilitiesTotal)) * 100)}% of the total.`}
            </Text>
          </View>
        )}
      </View>

      {/* ── Content ── */}
      <View style={styles.content}>
        {/* Task 2.1 — where the aggregated number comes from */}
        <LinkedBanksCard onChanged={handleRefresh} />

        {/* Task 4.10 — the health grade, broken into what drives it */}
        <HealthCard health={health} />

        {/* Cash Flow */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('wealth.cashflow')}</Text>

          <View style={styles.cashFlowCard}>
            <View style={styles.cashFlowBar}>
              <View style={[styles.cashFlowBarSegment, { flex: expensesPct, backgroundColor: COLORS.danger }]} />
              <View style={[styles.cashFlowBarSegment, { flex: savingsPct, backgroundColor: COLORS.accent }]} />
            </View>

            <View style={styles.cashFlowStatsRow}>
              <View style={styles.cashFlowStat}>
                <View style={[styles.cashFlowDot, { backgroundColor: COLORS.success }]} />
                <Text style={styles.cashFlowStatLabel}>{t('wealth.income')}</Text>
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
          <Text style={styles.sectionTitle}>{t('wealth.myDeposits')}</Text>
          {deposits.length === 0 ? (
            <Text style={styles.emptyText}>{t('wealth.noDepositsYet')}</Text>
          ) : (
            deposits.map((deposit) => <DepositCard key={deposit.deposit_id} deposit={deposit} />)
          )}
        </View>

        <View style={styles.sectionDivider} />

        {/* My Loans */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('wealth.myLoans')}</Text>
          {loans.length === 0 ? (
            <Text style={styles.emptyText}>{t('wealth.noLoans')}</Text>
          ) : (
            loans.map((loan) => <LoanCard key={loan.loan_id} loan={loan} />)
          )}
        </View>

        <View style={styles.sectionDivider} />

        {/* Smart Recommendations */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('wealth.recommendations')}</Text>
          <Text style={styles.sectionSubtitle}>{t('wealth.recsSubtitle')}</Text>

          {suppressedNote && <Text style={styles.emptyText}>{suppressedNote}</Text>}
          {recsError && (
            <Text style={styles.emptyText}>
              We couldn't load personalized recommendations right now. Pull down to refresh.
            </Text>
          )}
          {!suppressedNote && !recsError && recommendations.length === 0 && (
            <Text style={styles.emptyText}>{t('wealth.noRecs')}</Text>
          )}

          {recommendations.map((rec) => (
            <RecommendationCard
              key={rec.id}
              rec={rec}
              expanded={expandedRecId === rec.id}
              onToggle={() => setExpandedRecId((prev) => (prev === rec.id ? null : rec.id))}
              liveReason={liveReasons[rec.id]}
              loadingReason={reasonsLoading && !liveReasons[rec.id]}
              onStart={startFromRecommendation}
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

  // ── M4: richer recommendation cards ──
  priorityChip: { borderRadius: 999, paddingHorizontal: SPACING.sm, paddingVertical: 3 },
  priorityChipText: { fontSize: 9, fontWeight: '800', letterSpacing: 0.3 },

  recFactRow: { flexDirection: 'row', gap: SPACING.lg, marginTop: SPACING.md },
  recFact: { flex: 1 },
  recFactLabel: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  recFactValue: { ...TYPOGRAPHY.h4, color: COLORS.text, marginTop: 2 },

  confidenceBlock: { marginTop: SPACING.md },
  confidenceLabelRow: { flexDirection: 'row', alignItems: 'center', gap: SPACING.xs },
  confidenceTrack: {
    height: 5,
    borderRadius: 3,
    backgroundColor: COLORS.border,
    marginTop: SPACING.xs,
    overflow: 'hidden',
  },
  confidenceFill: { height: 5, borderRadius: 3 },

  recSource: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    marginTop: SPACING.xs,
    fontStyle: 'italic',
  },

  startBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.sm,
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.md,
    paddingVertical: SPACING.md,
    marginTop: SPACING.md,
  },
  startBtnText: { ...TYPOGRAPHY.bodyMedium, color: COLORS.textOnDark, fontWeight: '700' },

  nwBarWrap: { marginTop: SPACING.md },
  nwBar: { flexDirection: 'row', height: 8, borderRadius: 4, overflow: 'hidden' },
  nwBarAsset: { backgroundColor: COLORS.accent },
  nwBarLiability: { backgroundColor: COLORS.danger },
  nwBarCaption: { ...TYPOGRAPHY.caption, color: COLORS.textOnDarkSub, marginTop: SPACING.xs },

  // ── M4: financial health breakdown ──
  healthCard: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
  },
  healthHead: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: SPACING.md,
  },
  healthLabel: { ...TYPOGRAPHY.bodyMedium, color: COLORS.text },
  healthSub: { ...TYPOGRAPHY.caption, color: COLORS.textTertiary, marginTop: 1 },
  gradeBadge: {
    alignItems: 'center',
    borderWidth: 2,
    borderRadius: BORDER_RADIUS.md,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.xs,
  },
  gradeText: { ...TYPOGRAPHY.h2, lineHeight: 26 },
  gradeScore: { ...TYPOGRAPHY.caption, color: COLORS.textTertiary },

  componentRow: { flexDirection: 'row', alignItems: 'center', gap: SPACING.sm, marginTop: SPACING.sm },
  componentLabel: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary, width: 118 },
  componentTrack: {
    flex: 1,
    height: 6,
    borderRadius: 3,
    backgroundColor: COLORS.border,
    overflow: 'hidden',
  },
  componentFill: { height: 6, borderRadius: 3 },
  componentValue: { ...TYPOGRAPHY.caption, color: COLORS.textTertiary, width: 42, textAlign: 'right' },
  healthNote: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    marginTop: SPACING.md,
    lineHeight: 16,
  },
});

export default WealthOverviewScreen;