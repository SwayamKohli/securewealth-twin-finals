// src/screens/AuditDashboardScreen.tsx
// SecureWealth Twin — Security Audit Dashboard (Admin / Bank Officer Only)
//
// This screen is NOT part of the user-facing tab navigator. It is accessed
// via the admin modal stack (Profile tab -> Admin: Audit Dashboard button).
//
// Shows bank officers:
//   1. Summary counts (total events / verified / tamper attempts)
//   2. Hash chain visual (live from audit_logs.json hashes)
//   3. Audit log list (tap any row for detail sheet)
//   4. Detail sheet: replica verification, recovery events, tech fields
//
// Fixes from original:
//  - COLORS.warning -> COLORS.caution (Batch 1 semantic name)
//  - Three style strings had unclosed quotes: alignItems: 'center, -> fixed
//  - File was truncated mid-styles block -> completed
//  - FlatList inside ScrollView (virtualization warning) -> replaced with .map()
//  - Detail "modal" was a View inside ScrollView (not a real modal) -> proper Modal
//  - getIntegrityBadge returned RiskBadge with wrong semantic levels
//    (VERIFIED -> LOW is confusing for officers). Replaced with a proper
//    integrity badge component using direct color mapping.
//  - COLORS.warning references in decision coloring -> COLORS.caution
//  - HashChainVisual now receives replicaStatuses built from audit data

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Modal,
  RefreshControl,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import Card from '../components/common/Card';
import HashChainVisual, { ReplicaStatus } from '../components/common/HashChainVisual';
import auditLogsData from '../../mockData/audit_logs.json';

// ── Types ─────────────────────────────────────────────────────────────────────
type IntegrityStatus = 'VERIFIED' | 'TAMPER_DETECTED' | 'PENDING';
type AuditDecision = 'ALLOW' | 'BLOCK' | 'WARN' | 'CHALLENGE' | 'TAMPER_DETECTED';

// ── Helpers ───────────────────────────────────────────────────────────────────
const formatTime = (iso: string) =>
  new Date(iso).toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  });

const decisionColor = (d: string): string => {
  if (d === 'ALLOW') return COLORS.success;
  if (d === 'BLOCK') return COLORS.danger;
  if (d === 'TAMPER_DETECTED') return COLORS.danger;
  if (d === 'WARN') return COLORS.caution;
  if (d === 'CHALLENGE') return COLORS.challenge;
  return COLORS.textSecondary;
};

const decisionIcon = (d: string): string => {
  if (d === 'ALLOW') return 'check-circle';
  if (d === 'BLOCK') return 'x-circle';
  if (d === 'TAMPER_DETECTED') return 'alert-triangle';
  if (d === 'WARN') return 'alert-circle';
  return 'circle';
};

// Integrity badge — shows VERIFIED / TAMPER DETECTED / PENDING
// using direct colors rather than RiskBadge (which shows "Low Risk"/"Critical"
// — confusing in an audit officer context)
const IntegrityBadge = ({ status }: { status: string }) => {
  const isTampered = status === 'TAMPER_DETECTED';
  const isPending = status === 'PENDING';
  const color = isTampered ? COLORS.danger : isPending ? COLORS.caution : COLORS.success;
  const bg = isTampered ? COLORS.dangerLight : isPending ? COLORS.cautionLight : COLORS.success + '15';
  const icon = isTampered ? 'alert-triangle' : isPending ? 'clock' : 'check-circle';
  const label = isTampered ? 'Tampered' : isPending ? 'Pending' : 'Verified';

  return (
    <View style={[styles.integrityBadge, { backgroundColor: bg }]}>
      <Feather name={icon as any} size={11} color={color} />
      <Text style={[styles.integrityBadgeText, { color }]}>{label}</Text>
    </View>
  );
};

// ── Main Screen ───────────────────────────────────────────────────────────────
const AuditDashboardScreen = () => {
  const insets = useSafeAreaInsets();
  const [refreshing, setRefreshing] = useState(false);
  const [selectedAudit, setSelectedAudit] = useState<typeof auditLogsData[0] | null>(null);
  const [filterDecision, setFilterDecision] = useState<string>('ALL');

  const handleRefresh = async () => {
    setRefreshing(true);
    await new Promise((r) => setTimeout(r, 1200));
    setRefreshing(false);
  };

  // Summary counts
  const totalEvents = auditLogsData.length;
  const verifiedCount = auditLogsData.filter((l) => l.integrityStatus === 'VERIFIED').length;
  const tamperCount = auditLogsData.filter((l) => l.integrityStatus === 'TAMPER_DETECTED').length;

  // Filtered logs
  const filters = ['ALL', 'ALLOW', 'BLOCK', 'TAMPER_DETECTED'];
  const filteredLogs =
    filterDecision === 'ALL'
      ? auditLogsData
      : auditLogsData.filter((l) => l.decision === filterDecision);

  // Hash chain data from audit logs (most recent first -> reverse for chain order)
  const chainHashes = [...auditLogsData]
    .reverse()
    .map((l) => l.currentHash);

  // Find tampered index in the chain
  const tamperedChainIndex = [...auditLogsData]
    .reverse()
    .findIndex((l) => l.integrityStatus === 'TAMPER_DETECTED');

  // Build replica statuses from the first tampered record (for demo)
  const tamperedRecord = auditLogsData.find((l) => l.integrityStatus === 'TAMPER_DETECTED');
  const replicaStatuses: ReplicaStatus[] = tamperedRecord
    ? [
        { name: 'Replica A', matches: tamperedRecord.replicaVerification.replicaA === 'VERIFIED' },
        { name: 'Replica B', matches: tamperedRecord.replicaVerification.replicaB === 'VERIFIED' },
        { name: 'Replica C', matches: tamperedRecord.replicaVerification.replicaC === 'VERIFIED' },
      ]
    : [];

  return (
    <>
      <ScrollView
        style={styles.container}
        contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + SPACING.xl }]}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} tintColor={COLORS.primary} />
        }
      >
        {/* ── Summary row ── */}
        <View style={styles.summaryRow}>
          {[
            { icon: 'activity', label: 'Total Events', value: totalEvents, color: COLORS.primary },
            { icon: 'check-circle', label: 'Verified', value: verifiedCount, color: COLORS.success },
            { icon: 'alert-triangle', label: 'Tamper Attempts', value: tamperCount, color: COLORS.danger },
          ].map((item) => (
            <View key={item.label} style={styles.summaryCard}>
              <Feather name={item.icon as any} size={20} color={item.color} />
              <Text style={[styles.summaryValue, { color: item.color }]}>{item.value}</Text>
              <Text style={styles.summaryLabel}>{item.label}</Text>
            </View>
          ))}
        </View>

        {/* ── Integrity status card ── */}
        <Card style={styles.integrityCard} padding="lg">
          <View style={styles.integrityHeaderRow}>
            <View style={styles.integrityIconWrap}>
              <Feather name="lock" size={16} color={COLORS.success} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.integrityTitle}>Distributed Audit Ledger</Text>
              <Text style={styles.integritySubtitle}>
                Ed25519 signed · Hash chained · 3 replicas
              </Text>
            </View>
            <View style={[styles.integrityBadge, { backgroundColor: COLORS.success + '15' }]}>
              <Feather name="check-circle" size={11} color={COLORS.success} />
              <Text style={[styles.integrityBadgeText, { color: COLORS.success }]}>Active</Text>
            </View>
          </View>

          <View style={styles.integrityStatsRow}>
            {[
              { label: 'Replicas', value: '3' },
              { label: 'Availability', value: '100%' },
              { label: 'Integrity', value: `${Math.round((verifiedCount / totalEvents) * 100)}%` },
            ].map((s) => (
              <View key={s.label} style={styles.integrityStat}>
                <Text style={styles.integrityStatValue}>{s.value}</Text>
                <Text style={styles.integrityStatLabel}>{s.label}</Text>
              </View>
            ))}
          </View>
        </Card>

        {/* ── Hash chain visual ── */}
        <Card style={styles.section} padding="lg">
          <Text style={styles.sectionTitle}>Hash Chain Verification</Text>
          <HashChainVisual
            hashes={chainHashes}
            verifiedIndex={tamperedChainIndex >= 0 ? tamperedChainIndex - 1 : chainHashes.length - 1}
            tamperedIndex={tamperedChainIndex}
            replicaStatuses={replicaStatuses}
          />
        </Card>

        {/* ── Filter chips ── */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filterRow}
        >
          {filters.map((f) => (
            <TouchableOpacity
              key={f}
              style={[styles.filterChip, filterDecision === f && styles.filterChipActive]}
              onPress={() => setFilterDecision(f)}
              activeOpacity={0.7}
            >
              <Text style={[styles.filterChipText, filterDecision === f && styles.filterChipTextActive]}>
                {f.replace('_', ' ')}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* ── Audit log list ── */}
        <Card style={styles.section} padding="lg">
          <View style={styles.sectionHeaderRow}>
            <Text style={styles.sectionTitle}>Audit Events</Text>
            <Text style={styles.sectionCount}>{filteredLogs.length} records</Text>
          </View>

          {filteredLogs.map((log) => (
            <TouchableOpacity
              key={log.auditId}
              style={styles.logRow}
              onPress={() => setSelectedAudit(log)}
              activeOpacity={0.7}
            >
              <View style={styles.logIconWrap}>
                <Feather
                  name={decisionIcon(log.decision) as any}
                  size={18}
                  color={decisionColor(log.decision)}
                />
              </View>
              <View style={styles.logContent}>
                <View style={styles.logTopRow}>
                  <Text style={styles.logId}>{log.auditId}</Text>
                  <Text style={styles.logTime}>
                    {new Date(log.timestamp).toLocaleTimeString('en-IN', {
                      hour: '2-digit',
                      minute: '2-digit',
                      hour12: true,
                    })}
                  </Text>
                </View>
                <Text style={styles.logEventType}>
                  {log.eventType.replace(/_/g, ' ')}
                </Text>
                <View style={styles.logBottomRow}>
                  <Text style={[styles.logDecision, { color: decisionColor(log.decision) }]}>
                    {log.decision.replace('_', ' ')}
                  </Text>
                  <Text style={styles.logRisk}>Risk: {log.riskScore}/100</Text>
                  <IntegrityBadge status={log.integrityStatus} />
                </View>
              </View>
              <Feather name="chevron-right" size={16} color={COLORS.textTertiary} />
            </TouchableOpacity>
          ))}
        </Card>

        {/* ── Security features ── */}
        <Card style={styles.section} padding="lg">
          <Text style={styles.sectionTitle}>Audit Architecture</Text>
          {[
            { icon: 'hash', text: 'SHA-256 hash chaining — any modification breaks the chain' },
            { icon: 'key', text: 'Ed25519 digital signatures — only Audit Service holds the private key' },
            { icon: 'database', text: '3 distributed replicas — majority consensus detects tampering' },
            { icon: 'refresh-cw', text: 'Automatic recovery — corrupted records restored from replicas' },
          ].map((item, i) => (
            <View key={i} style={styles.featureRow}>
              <View style={styles.featureIconWrap}>
                <Feather name={item.icon as any} size={15} color={COLORS.primary} />
              </View>
              <Text style={styles.featureText}>{item.text}</Text>
            </View>
          ))}
        </Card>
      </ScrollView>

      {/* ── Detail Modal ── */}
      <Modal
        visible={!!selectedAudit}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setSelectedAudit(null)}
      >
        {selectedAudit && (
          <View style={styles.modalRoot}>
            {/* Modal header */}
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Audit Record</Text>
              <TouchableOpacity
                onPress={() => setSelectedAudit(null)}
                style={styles.modalCloseBtn}
                hitSlop={8}
              >
                <Feather name="x" size={22} color={COLORS.text} />
              </TouchableOpacity>
            </View>

            <ScrollView
              contentContainerStyle={styles.modalScroll}
              showsVerticalScrollIndicator={false}
            >
              {/* Decision banner */}
              <View
                style={[
                  styles.decisionBanner,
                  { backgroundColor: decisionColor(selectedAudit.decision) + '15' },
                ]}
              >
                <Feather
                  name={decisionIcon(selectedAudit.decision) as any}
                  size={24}
                  color={decisionColor(selectedAudit.decision)}
                />
                <View style={{ flex: 1 }}>
                  <Text style={[styles.decisionBannerTitle, { color: decisionColor(selectedAudit.decision) }]}>
                    {selectedAudit.decision.replace(/_/g, ' ')}
                  </Text>
                  <Text style={styles.decisionBannerSub}>{formatTime(selectedAudit.timestamp)}</Text>
                </View>
                <IntegrityBadge status={selectedAudit.integrityStatus} />
              </View>

              {/* Core fields */}
              <Card padding="lg" style={styles.detailCard}>
                <Text style={styles.detailCardTitle}>Event Details</Text>
                {[
                  { label: 'Audit ID', value: selectedAudit.auditId },
                  { label: 'User ID', value: selectedAudit.userId },
                  { label: 'Event Type', value: selectedAudit.eventType.replace(/_/g, ' ') },
                  { label: 'Risk Score', value: `${selectedAudit.riskScore} / 100` },
                  { label: 'Timestamp', value: formatTime(selectedAudit.timestamp) },
                ].map((row) => (
                  <View key={row.label} style={styles.detailRow}>
                    <Text style={styles.detailLabel}>{row.label}</Text>
                    <Text style={styles.detailValue}>{row.value}</Text>
                  </View>
                ))}
              </Card>

              {/* Event context */}
              <Card padding="lg" style={styles.detailCard}>
                <Text style={styles.detailCardTitle}>Context</Text>
                {Object.entries(selectedAudit.eventDetails).map(([k, v]) => (
                  <View key={k} style={styles.detailRow}>
                    <Text style={styles.detailLabel}>{k.replace(/([A-Z])/g, ' $1').trim()}</Text>
                    <Text style={styles.detailValue}>{String(v)}</Text>
                  </View>
                ))}
              </Card>

              {/* Hash chain */}
              <Card padding="lg" style={styles.detailCard}>
                <Text style={styles.detailCardTitle}>Cryptographic Record</Text>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Previous Hash</Text>
                  <Text style={styles.hashValue}>{selectedAudit.previousHash}</Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Current Hash</Text>
                  <Text style={styles.hashValue}>{selectedAudit.currentHash}</Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Signature</Text>
                  <Text style={styles.hashValue}>{selectedAudit.signature}</Text>
                </View>
              </Card>

              {/* Replica verification */}
              <Card padding="lg" style={styles.detailCard}>
                <Text style={styles.detailCardTitle}>Replica Verification</Text>
                {[
                  { label: 'Master', value: selectedAudit.replicaVerification.master },
                  { label: 'Replica A', value: selectedAudit.replicaVerification.replicaA },
                  { label: 'Replica B', value: selectedAudit.replicaVerification.replicaB },
                  { label: 'Replica C', value: selectedAudit.replicaVerification.replicaC },
                ].map((r) => (
                  <View key={r.label} style={styles.replicaRow}>
                    <Text style={styles.detailLabel}>{r.label}</Text>
                    <View style={styles.replicaStatusWrap}>
                      <Feather
                        name={r.value === 'VERIFIED' ? 'check-circle' : 'x-circle'}
                        size={14}
                        color={r.value === 'VERIFIED' ? COLORS.success : COLORS.danger}
                      />
                      <Text
                        style={[
                          styles.replicaStatusText,
                          { color: r.value === 'VERIFIED' ? COLORS.success : COLORS.danger },
                        ]}
                      >
                        {r.value}
                      </Text>
                    </View>
                  </View>
                ))}

                {/* Recovery event if present */}
                {'recoveryEvent' in selectedAudit.replicaVerification &&
                  selectedAudit.replicaVerification.recoveryEvent && (
                    <View style={styles.recoveryBanner}>
                      <Feather name="refresh-cw" size={14} color={COLORS.danger} />
                      <Text style={styles.recoveryText}>
                        Tamper detected — record automatically restored from{' '}
                        {(selectedAudit.replicaVerification.recoveryEvent as any).restoredFrom} at{' '}
                        {formatTime((selectedAudit.replicaVerification.recoveryEvent as any).timestamp)}
                      </Text>
                    </View>
                  )}
              </Card>

              <View style={{ height: SPACING.xxl }} />
            </ScrollView>
          </View>
        )}
      </Modal>
    </>
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

  // Summary
  summaryRow: {
    flexDirection: 'row',
    gap: SPACING.sm,
    marginBottom: SPACING.md,
  },
  summaryCard: {
    flex: 1,
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    alignItems: 'center',
    gap: SPACING.xs,
    ...SHADOWS.small,
  },
  summaryValue: {
    ...TYPOGRAPHY.h3,
    fontWeight: '700',
  },
  summaryLabel: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    textAlign: 'center',
  },

  // Integrity card
  integrityCard: {
    marginBottom: SPACING.md,
  },
  integrityHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginBottom: SPACING.md,
  },
  integrityIconWrap: {
    width: 34,
    height: 34,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.success + '15',
    justifyContent: 'center',
    alignItems: 'center',
  },
  integrityTitle: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.text,
    fontWeight: '700',
  },
  integritySubtitle: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    marginTop: 1,
  },
  integrityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    borderRadius: BORDER_RADIUS.full,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 3,
  },
  integrityBadgeText: {
    ...TYPOGRAPHY.captionBold,
  },
  integrityStatsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    borderTopWidth: 1,
    borderTopColor: COLORS.divider,
    paddingTop: SPACING.md,
  },
  integrityStat: {
    alignItems: 'center',
  },
  integrityStatValue: {
    ...TYPOGRAPHY.h4,
    color: COLORS.primary,
    fontWeight: '700',
  },
  integrityStatLabel: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    marginTop: 2,
  },

  // Generic section card
  section: {
    marginBottom: SPACING.md,
  },
  sectionTitle: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.text,
    fontWeight: '700',
    marginBottom: SPACING.md,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  sectionCount: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
  },

  // Filter chips
  filterRow: {
    gap: SPACING.sm,
    paddingBottom: SPACING.md,
  },
  filterChip: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.surfaceLight,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  filterChipActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  filterChipText: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.textSecondary,
  },
  filterChipTextActive: {
    color: COLORS.textOnDark,
  },

  // Log row
  logRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.md,
    paddingVertical: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
  },
  logIconWrap: {
    width: 36,
    height: 36,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.surfaceLight,
    justifyContent: 'center',
    alignItems: 'center',
    flexShrink: 0,
  },
  logContent: {
    flex: 1,
    minWidth: 0,
  },
  logTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 2,
  },
  logId: {
    ...TYPOGRAPHY.captionBold,
    color: COLORS.primary,
  },
  logTime: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
  },
  logEventType: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.text,
    fontWeight: '600',
    marginBottom: 4,
  },
  logBottomRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
  },
  logDecision: {
    ...TYPOGRAPHY.captionBold,
  },
  logRisk: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
  },

  // Feature rows
  featureRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: SPACING.sm,
    marginBottom: SPACING.sm,
  },
  featureIconWrap: {
    width: 28,
    height: 28,
    borderRadius: BORDER_RADIUS.sm,
    backgroundColor: COLORS.primaryVeryLight,
    justifyContent: 'center',
    alignItems: 'center',
    flexShrink: 0,
    marginTop: 1,
  },
  featureText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    flex: 1,
    lineHeight: 19,
  },

  // Detail modal
  modalRoot: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    backgroundColor: COLORS.surface,
  },
  modalTitle: {
    ...TYPOGRAPHY.h4,
    color: COLORS.text,
    fontWeight: '700',
  },
  modalCloseBtn: {
    padding: SPACING.xs,
  },
  modalScroll: {
    padding: SPACING.lg,
  },
  decisionBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.md,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    marginBottom: SPACING.md,
  },
  decisionBannerTitle: {
    ...TYPOGRAPHY.bodyMedium,
    fontWeight: '700',
  },
  decisionBannerSub: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textSecondary,
    marginTop: 1,
  },
  detailCard: {
    marginBottom: SPACING.md,
  },
  detailCardTitle: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.text,
    fontWeight: '700',
    marginBottom: SPACING.sm,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingVertical: SPACING.xs,
    borderTopWidth: 1,
    borderTopColor: COLORS.divider,
  },
  detailLabel: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    textTransform: 'capitalize',
    flex: 1,
  },
  detailValue: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.text,
    fontWeight: '600',
    flex: 1.5,
    textAlign: 'right',
  },
  hashValue: {
    ...TYPOGRAPHY.caption,
    color: COLORS.primary,
    fontFamily: 'monospace',
    flex: 1.5,
    textAlign: 'right',
  },
  replicaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: SPACING.xs,
    borderTopWidth: 1,
    borderTopColor: COLORS.divider,
  },
  replicaStatusWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  replicaStatusText: {
    ...TYPOGRAPHY.captionBold,
  },
  recoveryBanner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: SPACING.sm,
    backgroundColor: COLORS.dangerLight,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginTop: SPACING.md,
  },
  recoveryText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.danger,
    flex: 1,
    lineHeight: 19,
  },
});

export default AuditDashboardScreen;