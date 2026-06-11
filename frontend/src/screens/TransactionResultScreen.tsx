// src/screens/TransactionResultScreen.tsx
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import Card from '../components/common/Card';
import RiskBadge from '../components/common/RiskBadge';

const TransactionResultScreen = () => {
  // Mock transaction data
  const transactionResult = {
    decision: 'BLOCK' as const, // Options: ALLOW, WARN, REVIEW, BLOCK
    riskLevel: 'CRITICAL' as const,
    amount: 50000,
    fromAccount: '****1234',
    toAccount: '****5678',
    merchant: 'XYZ Company',
    timestamp: '2026-06-12T01:04:22Z',
    reason: 'Multiple suspicious signals detected',
    signals: [
      'New device detected',
      'Late-night transaction',
      'Fast OTP entry',
      'Amount spike detected'
    ],
    confidence: 98,
  };

  const getDecisionColors = () => {
    switch (transactionResult.decision) {
      case 'ALLOW':
        return { bg: COLORS.success + '20', text: COLORS.success, icon: 'check-circle' };
      case 'WARN':
        return { bg: COLORS.warning + '20', text: COLORS.warning, icon: 'alert-circle' };
      case 'REVIEW':
        return { bg: COLORS.warning + '20', text: COLORS.warning, icon: 'alert-triangle' };
      case 'BLOCK':
        return { bg: COLORS.danger + '20', text: COLORS.danger, icon: 'x-circle' };
      default:
        return { bg: COLORS.text + '20', text: COLORS.text, icon: 'info' };
    }
  };

  const decisionColors = getDecisionColors();

  const handleNewTransaction = () => {
    console.log('Starting new transaction...');
    // Navigate to transaction initiate screen
  };

  const handleViewHistory = () => {
    console.log('Viewing transaction history...');
    // Navigate to transaction history screen
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity>
          <Feather name="arrow-left" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Transaction Result</Text>
        <View style={{ width: 24 }} /> {/* Spacer */}
      </View>

      {/* Result Card */}
      <Card style={styles.resultCard}>
        <View style={[
          styles.resultIconContainer,
          { backgroundColor: decisionColors.bg }
        ]}>
          <Feather name={decisionColors.icon as any} size={48} color={decisionColors.text} />
        </View>
        
        <Text style={[
          styles.resultTitle,
          { color: decisionColors.text }
        ]}>
          {transactionResult.decision === 'ALLOW' ? 'Transaction Successful' :
           transactionResult.decision === 'WARN' ? 'Transaction Processed with Warning' :
           transactionResult.decision === 'REVIEW' ? 'Additional Verification Required' :
           'Transaction Blocked'}
        </Text>
        
        <Text style={styles.resultMessage}>
          {transactionResult.decision === 'ALLOW' ? 'Your transaction was processed successfully.' :
           transactionResult.decision === 'WARN' ? 'Your transaction was processed but flagged for review.' :
           transactionResult.decision === 'REVIEW' ? 'Additional verification is required to complete this transaction.' :
           'Your transaction was blocked for security reasons.'}
        </Text>

        {/* Risk Level */}
        <View style={styles.riskLevelContainer}>
          <Text style={styles.riskLabel}>Risk Level:</Text>
          <RiskBadge level={transactionResult.riskLevel} showIcon={true} size="md" />
        </View>
      </Card>

      {/* Transaction Details */}
      <Card style={styles.detailsCard}>
        <Text style={styles.sectionTitle}>Transaction Details</Text>
        
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Amount</Text>
          <Text style={styles.detailValue}>₹{transactionResult.amount.toLocaleString()}</Text>
        </View>
        
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>From Account</Text>
          <Text style={styles.detailValue}>{transactionResult.fromAccount}</Text>
        </View>
        
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>To Account</Text>
          <Text style={styles.detailValue}>{transactionResult.toAccount}</Text>
        </View>
        
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Time</Text>
          <Text style={styles.detailValue}>01:04 AM, Today</Text>
        </View>
        
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Status</Text>
          <Text style={[styles.detailValue, { color: decisionColors.text, fontWeight: '600' }]}>
            {transactionResult.decision}
          </Text>
        </View>
      </Card>

      {/* Security Analysis */}
      {transactionResult.signals && transactionResult.signals.length > 0 && (
        <Card style={styles.analysisCard}>
          <Text style={styles.sectionTitle}>Security Analysis</Text>
          
          <View style={styles.analysisItem}>
            <Feather name="shield" size={16} color={COLORS.text} />
            <Text style={styles.analysisText}>
              Risk Score: {transactionResult.confidence}/100
            </Text>
          </View>
          
          <View style={styles.analysisItem}>
            <Feather name="alert-triangle" size={16} color={COLORS.danger} />
            <Text style={styles.analysisText}>
              Reason: {transactionResult.reason}
            </Text>
          </View>
          
          <View style={styles.signalsContainer}>
            <Text style={styles.signalsLabel}>Detected Signals:</Text>
            {transactionResult.signals.map((signal, index) => (
              <View key={index} style={styles.signalItem}>
                <Feather name="x" size={12} color={COLORS.danger} />
                <Text style={styles.signalText}>{signal}</Text>
              </View>
            ))}
          </View>
        </Card>
      )}

      {/* Action Buttons */}
      <View style={styles.buttonContainer}>
        <TouchableOpacity 
          style={styles.primaryButton}
          onPress={handleNewTransaction}
        >
          <Feather name="plus" size={20} color={COLORS.textOnDark} />
          <Text style={styles.primaryButtonText}>New Transaction</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={styles.secondaryButton}
          onPress={handleViewHistory}
        >
          <Feather name="history" size={20} color={COLORS.primary} />
          <Text style={styles.secondaryButtonText}>View History</Text>
        </TouchableOpacity>
      </View>

      {/* Security Message */}
      {transactionResult.decision === 'BLOCK' && (
        <Card style={styles.securityCard}>
          <View style={styles.securityHeader}>
            <Feather name="shield" size={20} color={COLORS.success} />
            <Text style={styles.securityTitle}>Account Security</Text>
          </View>
          <Text style={styles.securityMessage}>
            Your account is safe. This transaction was stopped before any funds were transferred. 
            We continuously monitor for suspicious activity to protect your finances.
          </Text>
        </Card>
      )}

      {/* Additional Info */}
      <Card style={styles.infoCard}>
        <Text style={styles.infoTitle}>Need Help?</Text>
        <Text style={styles.infoText}>
          If you believe this decision was made in error, please contact our security team 
          or visit the nearest branch for assistance.
        </Text>
        <TouchableOpacity style={styles.contactButton}>
          <Feather name="phone" size={16} color={COLORS.primary} />
          <Text style={styles.contactText}>Contact Security Team</Text>
        </TouchableOpacity>
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
  resultCard: {
    alignItems: 'center',
    padding: SPACING.xl,
    marginBottom: SPACING.lg,
  },
  resultIconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  resultTitle: {
    ...TYPOGRAPHY.h2,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: SPACING.sm,
  },
  resultMessage: {
    ...TYPOGRAPHY.body,
    textAlign: 'center',
    color: COLORS.textSecondary,
    marginBottom: SPACING.lg,
  },
  riskLevelContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  riskLabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginRight: SPACING.sm,
  },
  detailsCard: {
    padding: SPACING.lg,
    marginBottom: SPACING.lg,
  },
  sectionTitle: {
    ...TYPOGRAPHY.h4,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  detailLabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
  },
  detailValue: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.text,
  },
  analysisCard: {
    padding: SPACING.lg,
    marginBottom: SPACING.lg,
  },
  analysisItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  analysisText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.text,
    marginLeft: SPACING.sm,
  },
  signalsContainer: {
    marginTop: SPACING.md,
  },
  signalsLabel: {
    ...TYPOGRAPHY.bodySm,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  signalItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surfaceLight,
    padding: SPACING.sm,
    borderRadius: BORDER_RADIUS.sm,
    marginBottom: SPACING.xs,
  },
  signalText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.text,
    marginLeft: SPACING.sm,
  },
  buttonContainer: {
    gap: SPACING.sm,
    marginBottom: SPACING.md,
  },
  primaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    padding: SPACING.lg,
    borderRadius: BORDER_RADIUS.lg,
  },
  primaryButtonText: {
    ...TYPOGRAPHY.button,
    color: COLORS.textOnDark,
    marginLeft: SPACING.sm,
  },
  secondaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.surface,
    padding: SPACING.lg,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  secondaryButtonText: {
    ...TYPOGRAPHY.button,
    color: COLORS.primary,
    marginLeft: SPACING.sm,
  },
  securityCard: {
    padding: SPACING.lg,
    marginBottom: SPACING.md,
  },
  securityHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  securityTitle: {
    ...TYPOGRAPHY.h4,
    fontWeight: '600',
    color: COLORS.text,
    marginLeft: SPACING.sm,
  },
  securityMessage: {
    ...TYPOGRAPHY.body,
    color: COLORS.text,
    lineHeight: 20,
  },
  infoCard: {
    padding: SPACING.lg,
  },
  infoTitle: {
    ...TYPOGRAPHY.h4,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  infoText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginBottom: SPACING.md,
    lineHeight: 18,
  },
  contactButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.surfaceLight,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
  },
  contactText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.primary,
    fontWeight: '600',
    marginLeft: SPACING.sm,
  },
});

export default TransactionResultScreen;