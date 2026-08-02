// src/screens/MySecurityActivityScreen.tsx
// SecureWealth Twin — My Security Activity (customer-facing)
//
// LIVE DATA: GET /api/v1/security/my-activity returns this customer's own
// security decisions, sourced from the immutable audit chain and already
// translated to plain language by the backend. This is NOT the admin audit
// dashboard (that is a standalone web app) — no hashes, no signatures, no
// other customers.
//
// M5 polish (task 13):
//   • Grouped by day ("Today", "Yesterday", "12 Jun") instead of one flat list
//   • Amount and fund shown as structured fields, not glued into the title
//   • A "REPORTED" state for investments the customer stopped themselves
//   • Fixed: the tamper badge compared against 'VERIFIED' while the value was
//     'VALID', so every record — including healthy ones — showed a warning.

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import { api } from '../api/apiService';
import { useI18n } from '../i18n';
import { ActivitySkeleton } from '../components/common/Skeleton';

type ActivityEntry = {
  id: string;
  timestamp: string;
  icon: string;
  iconColor: string;
  iconBg: string;
  title: string;
  detail: string;
  amount: number | null;
  fundName: string | null;
  tamperProtected: boolean;
};

interface ApiActivity {
  id: string;
  timestamp: string | null;
  decision: string;
  title: string;
  detail: string;
  status: string;
  amount: number | null;
  fund_name: string | null;
  tamper_protected: boolean;
}

const DECISION_VISUALS: Record<string, { icon: string; color: string; bg: string }> = {
  ALLOW: { icon: 'check-circle', color: COLORS.success, bg: '#DCFCE7' },
  WARN: { icon: 'alert-triangle', color: '#F59E0B', bg: '#FEF3C7' },
  CHALLENGE: { icon: 'shield', color: '#6366F1', bg: '#E0E7FF' },
  BLOCK: { icon: 'x-circle', color: '#DC2626', bg: '#FEE2E2' },
};

// The customer stopping an investment themselves (task 4.3c) is recorded with
// decision=BLOCK, but it deserves its own visual — they did this, we didn't.
const STATUS_VISUALS: Record<string, { icon: string; color: string; bg: string }> = {
  REPORTED: { icon: 'shield-off', color: '#DC2626', bg: '#FEE2E2' },
};

const translateLog = (log: ApiActivity): ActivityEntry => {
  const v =
    STATUS_VISUALS[String(log.status).toUpperCase()] ||
    DECISION_VISUALS[log.decision] ||
    DECISION_VISUALS.ALLOW;
  return {
    id: log.id,
    timestamp: log.timestamp || new Date().toISOString(),
    icon: v.icon,
    iconColor: v.color,
    iconBg: v.bg,
    title: log.title,
    detail: log.detail,
    amount: log.amount,
    fundName: log.fund_name,
    tamperProtected: !!log.tamper_protected,
  };
};

const formatCurrency = (n: number) => '₹' + Math.round(n).toLocaleString('en-IN');

/** Day bucket label used for section headers. */
const dayLabel = (iso: string, t: (k: string) => string): string => {
  const date = new Date(iso);
  const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  const diffD = Math.round((startOfDay(new Date()) - startOfDay(date)) / 86400000);

  if (diffD === 0) return t('common.today');
  if (diffD === 1) return t('common.yesterday');
  if (diffD < 7) return `${diffD} days ago`;
  return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
};

const formatTime = (iso: string): string =>
  new Date(iso).toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  });

// ── Main Screen ───────────────────────────────────────────────────────────────
const MySecurityActivityScreen = () => {
  const { t } = useI18n();
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [activities, setActivities] = useState<ActivityEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const res = await api.getMySecurityActivity();
      setActivities((res.activities || []).map(translateLog));
    } catch {
      setError(t('common.pullToRetry'));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [t]);

  useEffect(() => {
    load();
  }, [load]);

  // Group into day buckets, preserving the newest-first order the API returns.
  const groups = useMemo(() => {
    const out: { label: string; items: ActivityEntry[] }[] = [];
    for (const item of activities) {
      const label = dayLabel(item.timestamp, t);
      const last = out[out.length - 1];
      if (last && last.label === label) last.items.push(item);
      else out.push({ label, items: [item] });
    }
    return out;
  }, [activities, t]);

  if (loading) return <ActivitySkeleton />;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
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
      {/* Reassurance banner — what "protected" actually means, in one line */}
      <View style={styles.banner}>
        <Feather name="shield" size={16} color={COLORS.success} />
        <Text style={styles.bannerText}>
          {t('activity.banner')}
        </Text>
      </View>

      {error && <Text style={styles.emptyText}>{error}</Text>}
      {!error && activities.length === 0 && (
        <Text style={styles.emptyText}>
          {t('activity.empty')}
        </Text>
      )}

      {groups.map((group) => (
        <View key={group.label}>
          <Text style={styles.dayHeader}>{group.label}</Text>

          {group.items.map((activity) => {
            const expanded = expandedId === activity.id;
            return (
              <TouchableOpacity
                key={activity.id}
                style={styles.activityRow}
                onPress={() => setExpandedId(expanded ? null : activity.id)}
                activeOpacity={0.7}
                accessibilityRole="button"
                accessibilityLabel={`${activity.title}. ${
                  expanded ? 'Collapse' : 'Expand'
                } for details.`}
              >
                <View style={[styles.activityIcon, { backgroundColor: activity.iconBg }]}>
                  <Feather name={activity.icon as any} size={18} color={activity.iconColor} />
                </View>

                <View style={styles.activityContent}>
                  <View style={styles.activityTopRow}>
                    <Text style={styles.activityTitle}>{activity.title}</Text>
                    <Feather
                      name={expanded ? 'chevron-up' : 'chevron-down'}
                      size={15}
                      color={COLORS.textTertiary}
                    />
                  </View>

                  {/* Amount and fund as their own line — scannable */}
                  {(activity.amount != null || activity.fundName) && (
                    <Text style={styles.activitySubject}>
                      {activity.amount != null ? formatCurrency(activity.amount) : ''}
                      {activity.amount != null && activity.fundName ? ' · ' : ''}
                      {activity.fundName || ''}
                    </Text>
                  )}

                  <View style={styles.activityMetaRow}>
                    <Text style={styles.activityTime}>{formatTime(activity.timestamp)}</Text>
                    <View style={styles.integrityRow}>
                      <Feather
                        name={activity.tamperProtected ? 'lock' : 'alert-triangle'}
                        size={11}
                        color={activity.tamperProtected ? COLORS.success : COLORS.caution}
                      />
                      <Text
                        style={[
                          styles.integrityText,
                          {
                            color: activity.tamperProtected ? COLORS.success : COLORS.caution,
                          },
                        ]}
                      >
                        {activity.tamperProtected
                          ? t('activity.protected')
                          : t('activity.rechecking')}
                      </Text>
                    </View>
                  </View>

                  {expanded && (
                    <View>
                      <Text style={styles.activityDetail}>{activity.detail}</Text>
                      <Text style={styles.activityFootnote}>
                        {activity.tamperProtected
                          ? t('activity.sealed')
                          : t('activity.recheckNote')}
                      </Text>
                    </View>
                  )}
                </View>
              </TouchableOpacity>
            );
          })}
        </View>
      ))}

      <View style={{ height: SPACING.xxl }} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  centerBox: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.background,
  },
  emptyText: {
    ...TYPOGRAPHY.body,
    color: COLORS.textSecondary,
    textAlign: 'center',
    padding: SPACING.xl,
  },
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollContent: {
    padding: SPACING.lg,
  },
  banner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: SPACING.sm,
    backgroundColor: COLORS.primaryVeryLight,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
  },
  bannerText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.primaryMedium,
    flex: 1,
    lineHeight: 19,
  },
  dayHeader: {
    ...TYPOGRAPHY.captionBold,
    color: COLORS.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.7,
    marginTop: SPACING.sm,
    marginBottom: SPACING.sm,
  },
  activityRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: SPACING.md,
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    ...SHADOWS.small,
  },
  activityIcon: {
    width: 40,
    height: 40,
    borderRadius: BORDER_RADIUS.full,
    justifyContent: 'center',
    alignItems: 'center',
    flexShrink: 0,
  },
  activityContent: {
    flex: 1,
    minWidth: 0,
  },
  activityTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: SPACING.sm,
    marginBottom: 3,
  },
  activityTitle: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.text,
    fontWeight: '600',
    flex: 1,
  },
  activitySubject: {
    ...TYPOGRAPHY.caption,
    color: COLORS.text,
    fontWeight: '700',
    marginBottom: 4,
  },
  activityMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: SPACING.xs,
  },
  activityTime: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
  },
  integrityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
  },
  integrityText: {
    ...TYPOGRAPHY.caption,
    fontWeight: '500',
  },
  activityDetail: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginTop: SPACING.sm,
    lineHeight: 19,
  },
  activityFootnote: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    marginTop: SPACING.xs,
    lineHeight: 16,
  },
});

export default MySecurityActivityScreen;
