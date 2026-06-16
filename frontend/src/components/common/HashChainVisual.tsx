// src/components/common/HashChainVisual.tsx
// SecureWealth Twin -- Hash Chain Visualiser (Admin / Audit Dashboard)
//
// Used exclusively on the AuditDashboardScreen (Batch 8) to show bank officers
// how the Ed25519-signed hash chain works. Never shown to regular users.
//
// Changes from original:
//  - Chain now scrolls horizontally when there are many hashes, rather than
//    wrapping to new lines (which made the chain visual confusing).
//  - Each node displays first 6 + last 4 chars separated by "..." instead
//    of just the first 8, making it easier to distinguish adjacent hashes.
//  - Added replica status rows (Replica A/B/C match/mismatch indicators),
//    since the AuditDashboard needs to display all four tables (master + 3
//    replicas) as described in the blueprint's SecureLedger section.
//  - `tampered` prop marks a node red so demo scenarios can show tampering.

import React from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS } from '../../constants/theme';

export interface ReplicaStatus {
  name: string;  // e.g. "Replica A"
  matches: boolean;
}

interface HashChainVisualProps {
  /** Ordered array of truncated hash strings (master chain) */
  hashes: string[];
  /** Index up to which hashes are verified (-1 = none verified yet) */
  verifiedIndex?: number;
  /** Index of a tampered node (-1 = no tampering) */
  tamperedIndex?: number;
  /** Optional replica match statuses for the audit table visual */
  replicaStatuses?: ReplicaStatus[];
}

// Format hash for display: first 6 + "..." + last 4 chars
const shortHash = (h: string): string => {
  if (h.length <= 12) return h;
  return `${h.slice(0, 6)}...${h.slice(-4)}`;
};

const HashChainVisual: React.FC<HashChainVisualProps> = ({
  hashes,
  verifiedIndex = -1,
  tamperedIndex = -1,
  replicaStatuses,
}) => {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Hash Chain</Text>

      {/* Horizontal scrolling chain */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.chain}
      >
        {hashes.map((hash, index) => {
          const verified = verifiedIndex >= index;
          const tampered = tamperedIndex === index;

          const nodeColor = tampered
            ? COLORS.danger
            : verified
            ? COLORS.success
            : COLORS.textTertiary;

          const nodeBg = tampered
            ? COLORS.dangerLight
            : verified
            ? COLORS.success + '12'
            : COLORS.surfaceLight;

          return (
            <View key={index} style={styles.nodeWrap}>
              <View style={[styles.hashNode, { backgroundColor: nodeBg, borderColor: nodeColor }]}>
                <Feather
                  name={tampered ? 'alert-triangle' : verified ? 'check-circle' : 'circle'}
                  size={12}
                  color={nodeColor}
                />
                <Text style={[styles.hashText, { color: nodeColor }]}>
                  {shortHash(hash)}
                </Text>
              </View>

              {/* Arrow between nodes */}
              {index < hashes.length - 1 && (
                <Feather
                  name="arrow-right"
                  size={14}
                  color={COLORS.textTertiary}
                  style={styles.arrow}
                />
              )}
            </View>
          );
        })}
      </ScrollView>

      {/* Status summary */}
      <Text style={styles.status}>
        {tamperedIndex >= 0
          ? `Tampering detected at record ${tamperedIndex + 1}`
          : verifiedIndex === -1
          ? 'Verification not yet run'
          : verifiedIndex >= hashes.length - 1
          ? 'All records verified'
          : `Verified ${verifiedIndex + 1} of ${hashes.length} records`}
      </Text>

      {/* Replica status rows */}
      {replicaStatuses && replicaStatuses.length > 0 && (
        <View style={styles.replicaSection}>
          <Text style={styles.replicaTitle}>Replica Verification</Text>
          {replicaStatuses.map((r) => (
            <View key={r.name} style={styles.replicaRow}>
              <Feather
                name={r.matches ? 'check-circle' : 'x-circle'}
                size={14}
                color={r.matches ? COLORS.success : COLORS.danger}
              />
              <Text style={styles.replicaName}>{r.name}</Text>
              <Text
                style={[
                  styles.replicaStatus,
                  { color: r.matches ? COLORS.success : COLORS.danger },
                ]}
              >
                {r.matches ? 'Matches master' : 'Mismatch detected'}
              </Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.surfaceLight,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
  },
  title: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.text,
    fontWeight: '700',
    marginBottom: SPACING.md,
  },
  chain: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingBottom: SPACING.xs,
  },
  nodeWrap: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  hashNode: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
    paddingHorizontal: SPACING.sm,
    paddingVertical: SPACING.xs,
    borderRadius: BORDER_RADIUS.full,
    borderWidth: 1,
  },
  hashText: {
    ...TYPOGRAPHY.caption,
    fontFamily: 'monospace',
  },
  arrow: {
    marginHorizontal: SPACING.xs,
  },
  status: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textSecondary,
    marginTop: SPACING.md,
  },
  replicaSection: {
    marginTop: SPACING.md,
    borderTopWidth: 1,
    borderTopColor: COLORS.divider,
    paddingTop: SPACING.md,
  },
  replicaTitle: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: SPACING.sm,
  },
  replicaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginBottom: SPACING.xs,
  },
  replicaName: {
    ...TYPOGRAPHY.caption,
    color: COLORS.text,
    fontWeight: '600',
    width: 72,
  },
  replicaStatus: {
    ...TYPOGRAPHY.caption,
    fontWeight: '500',
  },
});

export default HashChainVisual;