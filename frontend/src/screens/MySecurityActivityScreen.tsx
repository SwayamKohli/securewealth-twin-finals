// src/screens/MySecurityActivityScreen.tsx
// SecureWealth Twin — My Security Activity (User-facing)
//
// ⚠️ BACKEND FLAG: The Master API Documentation (Finals Architecture Freeze v2)
// has no user-facing audit/activity endpoint — only the internal decision
// (/security/decision/make) and explainability endpoints, which return
// single-event objects, not a listable history. There is nothing like
// GET /audit/me or GET /users/me/activity to page through.
//
// Until that endpoint exists, this screen stays on mockData/audit_logs.json
// unchanged. When it's added, swap the two lines below:
//   import auditLogsData from '../../mockData/audit_logs.json';
//   const activities = [...auditLogsData]...
// for something like:
//   const logs = await api.getMyActivity();   // new endpoint, TBD shape
//   const activities = logs.map(translateLog);
// translateLog() already expects the same auditId/timestamp/eventType/
// eventDetails/integrityStatus shape as audit_logs.json, so a real backend
// response with matching fields should need no further changes here.
//
// Shows the current user's own security events in plain English.
// This is NOT the admin AuditDashboard — it shows user-friendly descriptions
// of what happened to their account, not raw technical audit fields.
//
// Data: audit_logs.json (filtered to USR-001 for mock)
// Each event is translated to plain English per the blueprint's
// "Explainability Philosophy" — every action must answer in human terms.

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import auditLogsData from '../../mockData/audit_logs.json';

// ── Plain-English translation layer ──────────────────────────────────────────
// Maps internal event types + decisions to what a regular user should see.
// (Bank officers see raw event types in AuditDashboard — this is different.)

type ActivityEntry = {
  id: string;
  timestamp: string;
  icon: string;
  iconColor: string;
  iconBg: string;
  title: string;
  detail: string;
  integrityStatus: string;
};

const translateLog = (log: typeof auditLogsData[0]): ActivityEntry => {
  const base = {
    id: log.auditId,
    timestamp: log.timestamp,
    integrityStatus: log.integrityStatus,
  };

  if (log.eventType === 'BLOCK_TRANSACTION') {
    const amount = (log.eventDetails as any).amount;
    const recipient = (log.eventDetails as any).recipient ?? (log.eventDetails as any).merchant;
    return {
      ...base,
      icon: 'shield',
      iconColor: COLORS.danger,
      iconBg: COLORS.dangerLight,
      title: 'A payment was stopped for your safety',
      detail: `We blocked a payment of \u20B9${Number(amount).toLocaleString('en-IN')} to ${recipient}. No money left your account.`,
    };
  }

  if (log.eventType === 'ALLOW_TRANSACTION') {
    const amount = (log.eventDetails as any).amount;
    const recipient = (log.eventDetails as any).recipient ?? (log.eventDetails as any).merchant;
    return {
      ...base,
      icon: 'check-circle',
      iconColor: COLORS.success,
      iconBg: COLORS.success + '15',
      title: 'Payment completed',
      detail: `\u20B9${Number(amount).toLocaleString('en-IN')} sent to ${recipient}.`,
    };
  }

  if (log.eventType === 'ALLOW_LOGIN') {
    const device = (log.eventDetails as any).device ?? 'your device';
    const location = (log.eventDetails as any).location ?? '';
    return {
      ...base,
      icon: 'log-in',
      iconColor: COLORS.primary,
      iconBg: COLORS.primaryVeryLight,
      title: 'You logged in',
      detail: `Login from ${device}${location ? ` in ${location}` : ''}.`,
    };
  }

  if (log.eventType === 'TAMPER_ATTEMPT') {
    return {
      ...base,
      icon: 'alert-triangle',
      iconColor: COLORS.caution,
      iconBg: COLORS.cautionLight,
      title: 'Unusual activity detected and resolved',
      detail:
        'Our security system detected and automatically corrected an irregularity in your security records. Your account is safe.',
    };
  }

  // Fallback for any future event types
  return {
    ...base,
    icon: 'info',
    iconColor: COLORS.info,
    iconBg: COLORS.info + '15',
    title: log.eventType.replace(/_/g, ' '),
    detail: `Security event recorded on your account.`,
  };
};

const formatRelativeTime = (iso: string): string => {
  const date = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffH = Math.floor(diffMs / (1000 * 60 * 60));
  const diffD = Math.floor(diffH / 24);

  if (diffD === 0) return 'Today';
  if (diffD === 1) return 'Yesterday';
  if (diffD < 7) return `${diffD} days ago`;
  return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
};

const formatTime = (iso: string): string =>
  new Date(iso).toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  });

// ── Main Screen ───────────────────────────────────────────────────────────────
const MySecurityActivityScreen = () => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Translate all logs to user-friendly entries, most recent first
  const activities = [...auditLogsData]
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .map(translateLog);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
    >
      {/* Reassurance banner */}
      <View style={styles.banner}>
        <Feather name="shield" size={16} color={COLORS.success} />
        <Text style={styles.bannerText}>
          Every action on your account is recorded and protected.
        </Text>
      </View>

      {/* Activity list */}
      {activities.map((activity) => {
        const expanded = expandedId === activity.id;
        return (
          <TouchableOpacity
            key={activity.id}
            style={styles.activityRow}
            onPress={() => setExpandedId(expanded ? null : activity.id)}
            activeOpacity={0.7}
          >
            {/* Icon */}
            <View style={[styles.activityIcon, { backgroundColor: activity.iconBg }]}>
              <Feather name={activity.icon as any} size={18} color={activity.iconColor} />
            </View>

            {/* Content */}
            <View style={styles.activityContent}>
              <View style={styles.activityTopRow}>
                <Text style={styles.activityTitle}>{activity.title}</Text>
                <Feather
                  name={expanded ? 'chevron-up' : 'chevron-down'}
                  size={15}
                  color={COLORS.textTertiary}
                />
              </View>

              <View style={styles.activityMetaRow}>
                <Text style={styles.activityTime}>
                  {formatRelativeTime(activity.timestamp)} · {formatTime(activity.timestamp)}
                </Text>
                {/* Integrity status — plain English */}
                <View style={styles.integrityRow}>
                  <Feather
                    name={activity.integrityStatus === 'VERIFIED' ? 'check' : 'alert-triangle'}
                    size={11}
                    color={activity.integrityStatus === 'VERIFIED' ? COLORS.success : COLORS.caution}
                  />
                  <Text
                    style={[
                      styles.integrityText,
                      {
                        color:
                          activity.integrityStatus === 'VERIFIED' ? COLORS.success : COLORS.caution,
                      },
                    ]}
                  >
                    Securely recorded
                  </Text>
                </View>
              </View>

              {/* Expanded detail */}
              {expanded && (
                <Text style={styles.activityDetail}>{activity.detail}</Text>
              )}
            </View>
          </TouchableOpacity>
        );
      })}

      <View style={{ height: SPACING.xxl }} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollContent: {
    padding: SPACING.lg,
  },
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
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
    marginBottom: 4,
  },
  activityTitle: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.text,
    fontWeight: '600',
    flex: 1,
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
});

export default MySecurityActivityScreen;