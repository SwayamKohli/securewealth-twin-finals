// src/screens/AuditDashboardScreen.tsx
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, FlatList, RefreshControl } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import Card from '../components/common/Card';
import RiskBadge from '../components/common/RiskBadge';
import HashChainVisual from '../components/common/HashChainVisual';

const AuditDashboardScreen = () => {
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState('ALL');
  const [selectedAudit, setSelectedAudit] = useState<any>(null);

  // Mock audit data
  const auditLogs = [
    {
      id: 'AUD-501',
      timestamp: '2026-06-12T01:10:22Z',
      userId: 'USR-001',
      eventType: 'BLOCK_TRANSACTION',
      eventDetails: {
        transactionId: 'TXN-004',
        amount: 50000,
        merchant: 'XYZ Ltd',
        reason: 'New device + night owl + fast OTP'
      },
      previousHash: 'ABC123DEF456',
      currentHash: 'XYZ789GHI012',
      signature: 'SIG_AUD_001',
      riskScore: 92,
      decision: 'BLOCK',
      integrityStatus: 'VERIFIED' as const,
      replicaVerification: {
        master: 'VERIFIED',
        replicaA: 'VERIFIED',
        replicaB: 'VERIFIED',
        replicaC: 'VERIFIED'
      }
    },
    {
      id: 'AUD-502',
      timestamp: '2026-06-12T02:15:33Z',
      userId: 'USR-001',
      eventType: 'ALLOW_LOGIN',
      eventDetails: {
        ipAddress: '192.168.1.100',
        location: 'Delhi, India',
        device: 'iPhone 14 Pro'
      },
      previousHash: 'XYZ789GHI012',
      currentHash: 'JKL345MNO678',
      signature: 'SIG_AUD_002',
      riskScore: 12,
      decision: 'ALLOW',
      integrityStatus: 'VERIFIED' as const,
      replicaVerification: {
        master: 'VERIFIED',
        replicaA: 'VERIFIED',
        replicaB: 'VERIFIED',
        replicaC: 'VERIFIED'
      }
    },
    {
      id: 'AUD-503',
      timestamp: '2026-06-11T23:45:11Z',
      userId: 'USR-001',
      eventType: 'BLOCK_TRANSACTION',
      eventDetails: {
        transactionId: 'TXN-005',
        amount: 75000,
        merchant: 'FakeShop Online',
        reason: 'Phishing attempt detected'
      },
      previousHash: 'JKL345MNO678',
      currentHash: 'PQR901STU234',
      signature: 'SIG_AUD_003',
      riskScore: 98,
      decision: 'BLOCK',
      integrityStatus: 'TAMPER_DETECTED' as const,
      replicaVerification: {
        master: 'MODIFIED',
        replicaA: 'VERIFIED',
        replicaB: 'VERIFIED',
        replicaC: 'VERIFIED',
        recoveryEvent: {
          timestamp: '2026-06-12T00:00:00Z',
          restoredFrom: 'Replica A',
          alertGenerated: true
        }
      }
    },
    {
      id: 'AUD-504',
      timestamp: '2026-06-11T22:30:45Z',
      userId: 'USR-002',
      eventType: 'REVIEW_TRANSACTION',
      eventDetails: {
        transactionId: 'TXN-006',
        amount: 25000,
        merchant: 'Investment Firm',
        reason: 'Unknown merchant'
      },
      previousHash: 'PQR901STU234',
      currentHash: 'VWX567YZA890',
      signature: 'SIG_AUD_004',
      riskScore: 68,
      decision: 'REVIEW',
      integrityStatus: 'VERIFIED' as const,
      replicaVerification: {
        master: 'VERIFIED',
        replicaA: 'VERIFIED',
        replicaB: 'VERIFIED',
        replicaC: 'VERIFIED'
      }
    },
  ];

  const handleRefresh = async () => {
    setRefreshing(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    setRefreshing(false);
  };

  const getIntegrityColor = (status: string) => {
    switch (status) {
      case 'VERIFIED': return COLORS.success;
      case 'TAMPER_DETECTED': return COLORS.danger;
      case 'PENDING': return COLORS.warning;
      default: return COLORS.text;
    }
  };

  const getIntegrityBadge = (status: string) => {
    switch (status) {
      case 'VERIFIED': 
        return <RiskBadge level="LOW" showIcon={true} size="sm" />;
      case 'TAMPER_DETECTED': 
        return <RiskBadge level="CRITICAL" showIcon={true} size="sm" />;
      case 'PENDING': 
        return <RiskBadge level="MEDIUM" showIcon={true} size="sm" />;
      default: 
        return <RiskBadge level="LOW" showIcon={true} size="sm" />;
    }
  };

  const renderAuditItem = ({ item }: any) => (
    <TouchableOpacity 
      style={styles.auditItem}
      onPress={() => setSelectedAudit(item)}
    >
      <View style={styles.auditHeader}>
        <Text style={styles.auditId}>{item.id}</Text>
        <Text style={styles.auditTime}>{new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</Text>
      </View>
      
      <View style={styles.auditContent}>
        <View style={styles.auditTypeContainer}>
          <Feather 
            name={
              item.eventType.includes('BLOCK') ? 'x-circle' :
              item.eventType.includes('ALLOW') ? 'check-circle' :
              item.eventType.includes('REVIEW') ? 'alert-triangle' :
              'info'
            } 
            size={20} 
            color={
              item.eventType.includes('BLOCK') ? COLORS.danger :
              item.eventType.includes('ALLOW') ? COLORS.success :
              item.eventType.includes('REVIEW') ? COLORS.warning :
              COLORS.info
            } 
          />
          <Text style={styles.auditType}>{item.eventType.replace('_', ' ')}</Text>
        </View>
        
        <View style={styles.auditStatusContainer}>
          <Text style={[
            styles.auditDecision, 
            { 
              color: 
                item.decision === 'BLOCK' ? COLORS.danger :
                item.decision === 'ALLOW' ? COLORS.success :
                item.decision === 'REVIEW' ? COLORS.warning :
                COLORS.text
            }
          ]}>
            {item.decision}
          </Text>
          {getIntegrityBadge(item.integrityStatus)}
        </View>
      </View>
      
      <View style={styles.auditDetails}>
        <Text style={styles.auditDescription}>
          {item.eventDetails.reason || `Processed ${item.eventType.replace('_', ' ').toLowerCase()}`}
        </Text>
        <Text style={styles.auditRisk}>Risk: {item.riskScore}/100</Text>
      </View>
    </TouchableOpacity>
  );

  return (
    <ScrollView 
      style={styles.container} 
      contentContainerStyle={styles.contentContainer}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} tintColor={COLORS.primary} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity>
          <Feather name="arrow-left" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Audit Dashboard</Text>
        <TouchableOpacity>
          <Feather name="filter" size={24} color={COLORS.text} />
        </TouchableOpacity>
      </View>

      {/* Summary Cards */}
      <View style={styles.summaryContainer}>
        <Card style={styles.summaryCard}>
          <Feather name="activity" size={24} color={COLORS.primary} />
          <Text style={styles.summaryValue}>142</Text>
          <Text style={styles.summaryLabel}>Total Events</Text>
        </Card>
        
        <Card style={styles.summaryCard}>
          <Feather name="shield-check" size={24} color={COLORS.success} />
          <Text style={styles.summaryValue}>140</Text>
          <Text style={styles.summaryLabel}>Verified</Text>
        </Card>
        
        <Card style={styles.summaryCard}>
          <Feather name="alert-triangle" size={24} color={COLORS.danger} />
          <Text style={styles.summaryValue}>2</Text>
          <Text style={styles.summaryLabel}>Tamper Attempts</Text>
        </Card>
      </View>

      {/* Integrity Status */}
      <Card style={styles.integrityCard}>
        <View style={styles.integrityHeader}>
          <Feather name="lock" size={20} color={COLORS.success} />
          <Text style={styles.integrityTitle}>Integrity Status</Text>
        </View>
        <Text style={styles.integrityDescription}>
          All audit logs are secured with distributed verification. Any unauthorized modification is immediately detected and recovered.
        </Text>
        <View style={styles.integrityStats}>
          <View style={styles.integrityStat}>
            <Text style={styles.statValue}>3</Text>
            <Text style={styles.statLabel}>Replicas</Text>
          </View>
          <View style={styles.integrityStat}>
            <Text style={styles.statValue}>100%</Text>
            <Text style={styles.statLabel}>Availability</Text>
          </View>
          <View style={styles.integrityStat}>
            <Text style={styles.statValue}>99.9%</Text>
            <Text style={styles.statLabel}>Integrity</Text>
          </View>
        </View>
      </Card>

      {/* Hash Chain Visualization */}
      <Card style={styles.hashChainCard}>
        <Text style={styles.sectionTitle}>Hash Chain Verification</Text>
        <HashChainVisual 
          hashes={['ABC123', 'XYZ789', 'JKL345', 'PQR901']}
          currentHash="VWX567"
          verifiedIndex={3}
        />
      </Card>

      {/* Audit Logs */}
      <Card style={styles.logsCard}>
        <View style={styles.logsHeader}>
          <Text style={styles.sectionTitle}>Recent Audit Events</Text>
          <TouchableOpacity>
            <Text style={styles.viewAllText}>View All</Text>
          </TouchableOpacity>
        </View>
        
        <FlatList
          data={auditLogs}
          renderItem={renderAuditItem}
          keyExtractor={(item) => item.id}
          showsVerticalScrollIndicator={false}
        />
      </Card>

      {/* Selected Audit Detail Modal */}
      {selectedAudit && (
        <View style={styles.modalOverlay}>
          <Card style={styles.detailModal}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Audit Event Details</Text>
              <TouchableOpacity onPress={() => setSelectedAudit(null)}>
                <Feather name="x" size={24} color={COLORS.text} />
              </TouchableOpacity>
            </View>
            
            <ScrollView style={styles.modalContent}>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Event ID</Text>
                <Text style={styles.detailValue}>{selectedAudit.id}</Text>
              </View>
              
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Timestamp</Text>
                <Text style={styles.detailValue}>{new Date(selectedAudit.timestamp).toLocaleString()}</Text>
              </View>
              
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>User ID</Text>
                <Text style={styles.detailValue}>{selectedAudit.userId}</Text>
              </View>
              
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Event Type</Text>
                <Text style={styles.detailValue}>{selectedAudit.eventType}</Text>
              </View>
              
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Decision</Text>
                <Text style={[
                  styles.detailValue,
                  { 
                    color: 
                      selectedAudit.decision === 'BLOCK' ? COLORS.danger :
                      selectedAudit.decision === 'ALLOW' ? COLORS.success :
                      selectedAudit.decision === 'REVIEW' ? COLORS.warning :
                      COLORS.text
                  }
                ]}>
                  {selectedAudit.decision}
                </Text>
              </View>
              
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Risk Score</Text>
                <Text style={styles.detailValue}>{selectedAudit.riskScore}/100</Text>
              </View>
              
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Integrity Status</Text>
                <Text style={[
                  styles.detailValue,
                  { color: getIntegrityColor(selectedAudit.integrityStatus) }
                ]}>
                  {selectedAudit.integrityStatus}
                </Text>
              </View>
              
              <View style={styles.detailSection}>
                <Text style={styles.detailSectionTitle}>Event Details</Text>
                <Text style={styles.detailSectionContent}>
                  {JSON.stringify(selectedAudit.eventDetails, null, 2)}
                </Text>
              </View>
              
              <View style={styles.detailSection}>
                <Text style={styles.detailSectionTitle}>Replica Verification</Text>
                <View style={styles.replicaGrid}>
                  <View style={styles.replicaItem}>
                    <Text style={styles.replicaLabel}>Master:</Text>
                    <Text style={[
                      styles.replicaValue,
                      { color: selectedAudit.replicaVerification.master === 'VERIFIED' ? COLORS.success : COLORS.danger }
                    ]}>
                      {selectedAudit.replicaVerification.master}
                    </Text>
                  </View>
                  <View style={styles.replicaItem}>
                    <Text style={styles.replicaLabel}>Replica A:</Text>
                    <Text style={[
                      styles.replicaValue,
                      { color: selectedAudit.replicaVerification.replicaA === 'VERIFIED' ? COLORS.success : COLORS.danger }
                    ]}>
                      {selectedAudit.replicaVerification.replicaA}
                    </Text>
                  </View>
                  <View style={styles.replicaItem}>
                    <Text style={styles.replicaLabel}>Replica B:</Text>
                    <Text style={[
                      styles.replicaValue,
                      { color: selectedAudit.replicaVerification.replicaB === 'VERIFIED' ? COLORS.success : COLORS.danger }
                    ]}>
                      {selectedAudit.replicaVerification.replicaB}
                    </Text>
                  </View>
                  <View style={styles.replicaItem}>
                    <Text style={styles.replicaLabel}>Replica C:</Text>
                    <Text style={[
                      styles.replicaValue,
                      { color: selectedAudit.replicaVerification.replicaC === 'VERIFIED' ? COLORS.success : COLORS.danger }
                    ]}>
                      {selectedAudit.replicaVerification.replicaC}
                    </Text>
                  </View>
                </View>
                
                {selectedAudit.replicaVerification.recoveryEvent && (
                  <View style={styles.recoveryAlert}>
                    <Feather name="alert-triangle" size={16} color={COLORS.danger} />
                    <Text style={styles.recoveryText}>
                      Recovery Event: Modified record restored from {selectedAudit.replicaVerification.recoveryEvent.restoredFrom}
                    </Text>
                  </View>
                )}
              </View>
            </ScrollView>
          </Card>
        </View>
      )}

      {/* Security Features */}
      <Card style={styles.featuresCard}>
        <Text style={styles.featuresTitle}>Security Features</Text>
        <View style={styles.featureList}>
          <View style={styles.featureItem}>
            <Feather name="hash" size={20} color={COLORS.primary} />
            <Text style={styles.featureText}>Hash Chain Verification</Text>
          </View>
          <View style={styles.featureItem}>
            <Feather name="key" size={20} color={COLORS.primary} />
            <Text style={styles.featureText}>Ed25519 Digital Signatures</Text>
          </View>
          <View style={styles.featureItem}>
            <Feather name="database" size={20} color={COLORS.primary} />
            <Text style={styles.featureText}>Distributed Replica Verification</Text>
          </View>
          <View style={styles.featureItem}>
            <Feather name="refresh-ccw" size={20} color={COLORS.primary} />
            <Text style={styles.featureText}>Automatic Recovery System</Text>
          </View>
        </View>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  contentContainer: {
    padding: SPACING.lg,
    paddingBottom: SPACING.xxl,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.xl,
  },
  title: {
    ...TYPOGRAPHY.h3,
    fontWeight: '600',
    color: COLORS.text,
  },
  summaryContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: SPACING.lg,
  },
  summaryCard: {
    flex: 1,
    alignItems: 'center',
    padding: SPACING.lg,
    marginHorizontal: SPACING.xs,
  },
  summaryValue: {
    ...TYPOGRAPHY.h2,
    fontWeight: '700',
    color: COLORS.primary,
    marginVertical: SPACING.xs,
  },
  summaryLabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
  },
  integrityCard: {
    padding: SPACING.lg,
    marginBottom: SPACING.lg,
  },
  integrityHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  integrityTitle: {
    ...TYPOGRAPHY.h4,
    fontWeight: '600',
    color: COLORS.text,
    marginLeft: SPACING.sm,
  },
  integrityDescription: {
    ...TYPOGRAPHY.body,
    color: COLORS.textSecondary,
    marginBottom: SPACING.md,
  },
  integrityStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  integrityStat: {
    alignItems: 'center',
  },
  statValue: {
    ...TYPOGRAPHY.h3,
    fontWeight: '700',
    color: COLORS.primary,
  },
  statLabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginTop: SPACING.xs,
  },
  hashChainCard: {
    padding: SPACING.lg,
    marginBottom: SPACING.lg,
  },
  sectionTitle: {
    ...TYPOGRAPHY.h4,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  logsCard: {
    padding: SPACING.lg,
    marginBottom: SPACING.lg,
  },
  logsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  viewAllText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.primary,
    fontWeight: '600',
  },
  auditItem: {
    backgroundColor: COLORS.surface,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    marginBottom: SPACING.sm,
    ...SHADOWS.small,
  },
  auditHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  auditId: {
    ...TYPOGRAPHY.bodySm,
    fontWeight: '600',
    color: COLORS.text,
  },
  auditTime: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textSecondary,
  },
  auditContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  auditTypeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  auditType: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.text,
    marginLeft: SPACING.sm,
  },
  auditStatusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
  },
  auditDecision: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
  },
  auditDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  auditDescription: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    flex: 1,
  },
  auditRisk: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    fontWeight: '600',
  },
  modalOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  detailModal: {
    width: '90%',
    maxHeight: '80%',
    padding: SPACING.lg,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  modalTitle: {
    ...TYPOGRAPHY.h4,
    fontWeight: '600',
    color: COLORS.text,
  },
  modalContent: {
    maxHeight: '70%',
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  detailLabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    flex: 1,
  },
  detailValue: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.text,
    textAlign: 'right',
  },
  detailSection: {
    marginTop: SPACING.lg,
  },
  detailSectionTitle: {
    ...TYPOGRAPHY.bodySm,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  detailSectionContent: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textSecondary,
    fontFamily: 'monospace',
    backgroundColor: COLORS.surfaceLight,
    padding: SPACING.sm,
    borderRadius: BORDER_RADIUS.sm,
  },
  replicaGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.md,
  },
  replicaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    minWidth: '45%',
  },
  replicaLabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginRight: SPACING.xs,
  },
  replicaValue: {
    ...TYPOGRAPHY.bodySm,
    fontWeight: '600',
  },
  recoveryAlert: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.danger + '10',
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    marginTop: SPACING.md,
  },
  recoveryText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.danger,
    marginLeft: SPACING.sm,
  },
  featuresCard: {
    padding: SPACING.lg,
  },
  featuresTitle: {
    ...TYPOGRAPHY.h4,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  featureList: {
    gap: SPACING.sm,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    ...SHADOWS.small,
  },
  featureText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.text,
    marginLeft: SPACING.sm,
  },
});

export default AuditDashboardScreen;