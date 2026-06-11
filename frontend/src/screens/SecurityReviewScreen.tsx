// src/screens/SecurityReviewScreen.tsx
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import Card from '../components/common/Card';
import RiskBadge from '../components/common/RiskBadge';
import ExplainableAlert from '../components/common/ExplainableAlert';

const SecurityReviewScreen = () => {
  const [expandedSignal, setExpandedSignal] = useState<string | null>(null);

  // Mock security data
  const transactionData = {
    amount: 50000,
    fromAccount: '****1234',
    toAccount: '****5678',
    merchant: 'XYZ Company',
    timestamp: '2026-06-12T01:04:00Z',
  };

  const riskSignals = [
    {
      id: 'device',
      type: 'DEVICE',
      name: 'New Device',
      status: 'SUSPICIOUS',
      priority: 'HIGH',
      description: 'Transaction from unrecognized device (iPhone 14, Delhi)',
      explanation: 'We detected that this transaction is coming from a device that hasn\'t been used for banking activities before. This could indicate unauthorized access.',
      timestamp: '2026-06-12T01:03:00Z',
    },
    {
      id: 'time',
      type: 'TIME',
      name: 'Night Owl',
      status: 'SUSPICIOUS',
      priority: 'MEDIUM',
      description: 'Transaction at 01:04 IST - high-risk time window',
      explanation: 'Most legitimate transactions occur during daytime hours. Transactions late at night are statistically more likely to be fraudulent.',
      timestamp: '2026-06-12T01:04:00Z',
    },
    {
      id: 'otp',
      type: 'OTP',
      name: 'Fast OTP',
      status: 'SUSPICIOUS',
      priority: 'HIGH',
      description: 'OTP entered unusually fast (<5 seconds) - possible coercion',
      explanation: 'If someone enters an OTP immediately after receiving it, it might indicate they are being coerced by another person who is watching them.',
      timestamp: '2026-06-12T01:04:05Z',
    },
    {
      id: 'amount',
      type: 'AMOUNT',
      name: 'Amount Spike',
      status: 'SUSPICIOUS',
      priority: 'HIGH',
      description: '₹50,000 = 28x user\'s average transfer amount',
      explanation: 'This transaction amount is significantly higher than your usual spending patterns, which could indicate fraudulent activity.',
      timestamp: '2026-06-12T01:04:10Z',
    },
  ];

  const securityTimeline = [
    { time: '01:02', event: 'Login', status: 'NORMAL', icon: 'log-in' },
    { time: '01:03', event: 'New Device', status: 'SUSPICIOUS', icon: 'smartphone' },
    { time: '01:04', event: 'OTP Entered', status: 'SUSPICIOUS', icon: 'key' },
    { time: '01:04', event: 'Transfer Initiated', status: 'SUSPICIOUS', icon: 'send' },
    { time: '01:04', event: 'Risk Elevated', status: 'CRITICAL', icon: 'alert-triangle' },
    { time: '01:04', event: 'Transaction Blocked', status: 'BLOCKED', icon: 'x-circle' },
  ];

  const riskLevel = 'CRITICAL' as const;
  const decision = 'BLOCK' as const;

  const handleProceedAnyway = () => {
    Alert.alert(
      'Proceed with Caution',
      'This transaction has been flagged as high-risk. Are you sure you want to proceed?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Proceed Anyway', 
          style: 'destructive',
          onPress: () => {
            console.log('User chose to proceed despite risks');
            // Navigate to transaction result
          }
        }
      ]
    );
  };

  const handleContactSupport = () => {
    Alert.alert('Contact Support', 'Would you like to contact our security team?', [
      { text: 'Cancel', style: 'cancel' },
      { 
        text: 'Call Security Team', 
        onPress: () => console.log('Calling security team...')
      }
    ]);
  };

  const toggleSignal = (id: string) => {
    setExpandedSignal(expandedSignal === id ? null : id);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity>
          <Feather name="arrow-left" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Security Review</Text>
        <View style={{ width: 24 }} />
      </View>

      {/* Transaction Summary */}
      <Card style={styles.transactionCard}>
        <View style={styles.transactionHeader}>
          <Feather name="alert-triangle" size={24} color={COLORS.danger} />
          <Text style={styles.transactionTitle}>Transaction Review Required</Text>
        </View>
        
        <View style={styles.transactionDetails}>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Amount</Text>
            <Text style={styles.detailValue}>₹{transactionData.amount.toLocaleString()}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>From</Text>
            <Text style={styles.detailValue}>{transactionData.fromAccount}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>To</Text>
            <Text style={styles.detailValue}>{transactionData.toAccount}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Time</Text>
            <Text style={styles.detailValue}>01:04 AM</Text>
          </View>
        </View>
      </Card>

      {/* Risk Level */}
      <View style={styles.riskLevelContainer}>
        <Text style={styles.riskLevelLabel}>Risk Assessment:</Text>
        <RiskBadge level={riskLevel} showIcon={true} size="lg" />
      </View>

      {/* Decision */}
      <Card style={styles.decisionCard}>
        <View style={styles.decisionHeader}>
          <Feather name="x-circle" size={32} color={COLORS.danger} />
          <Text style={styles.decisionTitle}>Transaction Blocked</Text>
        </View>
        <Text style={styles.decisionMessage}>
          This transaction has been automatically blocked due to multiple suspicious signals.
        </Text>
        <Text style={styles.decisionExplanation}>
          Your account is safe. This transaction was stopped before any funds were transferred.
        </Text>
      </Card>

      {/* Security Timeline */}
      <Card style={styles.timelineCard}>
        <Text style={styles.sectionTitle}>Security Timeline</Text>
        <View style={styles.timeline}>
          {securityTimeline.map((item, index) => (
            <View key={index} style={styles.timelineItem}>
              <View style={[
                styles.timelineDot,
                { 
                  backgroundColor: 
                    item.status === 'NORMAL' ? COLORS.success : 
                    item.status === 'SUSPICIOUS' ? COLORS.warning : 
                    item.status === 'CRITICAL' ? COLORS.danger : 
                    COLORS.text
                }
              ]}>
                <Feather name={item.icon as any} size={12} color={COLORS.textOnDark} />
              </View>
              <View style={styles.timelineContent}>
                <Text style={styles.timelineTime}>{item.time}</Text>
                <Text style={styles.timelineEvent}>{item.event}</Text>
              </View>
            </View>
          ))}
        </View>
      </Card>

      {/* Risk Signals */}
      <Card style={styles.signalsCard}>
        <Text style={styles.sectionTitle}>Risk Signals Detected</Text>
        <View style={styles.signalsList}>
          {riskSignals.map((signal) => (
            <TouchableOpacity 
              key={signal.id} 
              style={styles.signalItem}
              onPress={() => toggleSignal(signal.id)}
            >
              <View style={styles.signalHeader}>
                <View style={[
                  styles.signalIcon,
                  { 
                    backgroundColor: 
                      signal.priority === 'HIGH' ? COLORS.danger + '20' : 
                      signal.priority === 'MEDIUM' ? COLORS.warning + '20' : 
                      COLORS.success + '20'
                  }
                ]}>
                  <Feather 
                    name={
                      signal.priority === 'HIGH' ? 'alert-triangle' : 
                      signal.priority === 'MEDIUM' ? 'alert-circle' : 
                      'info'
                    } 
                    size={16} 
                    color={
                      signal.priority === 'HIGH' ? COLORS.danger : 
                      signal.priority === 'MEDIUM' ? COLORS.warning : 
                      COLORS.success
                    } 
                  />
                </View>
                <View style={styles.signalInfo}>
                  <Text style={styles.signalName}>{signal.name}</Text>
                  <Text style={styles.signalDescription}>{signal.description}</Text>
                </View>
                <Feather 
                  name={expandedSignal === signal.id ? 'chevron-up' : 'chevron-down'} 
                  size={20} 
                  color={COLORS.textSecondary} 
                />
              </View>
              
              {expandedSignal === signal.id && (
                <View style={styles.signalDetails}>
                  <Text style={styles.signalExplanation}>{signal.explanation}</Text>
                  <View style={styles.signalMeta}>
                    <Text style={styles.signalTime}>{signal.timestamp}</Text>
                    <Text style={styles.signalPriority}>Priority: {signal.priority}</Text>
                  </View>
                </View>
              )}
            </TouchableOpacity>
          ))}
        </View>
      </Card>

      {/* Action Buttons */}
      <View style={styles.actionButtons}>
        <TouchableOpacity 
          style={styles.proceedButton}
          onPress={handleProceedAnyway}
        >
          <Feather name="arrow-right" size={20} color={COLORS.textOnDark} />
          <Text style={styles.proceedButtonText}>Proceed Anyway</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={styles.supportButton}
          onPress={handleContactSupport}
        >
          <Feather name="headphones" size={20} color={COLORS.textOnDark} />
          <Text style={styles.supportButtonText}>Contact Security Team</Text>
        </TouchableOpacity>
      </View>

      {/* Security Alert */}
      <ExplainableAlert
        type="info"
        title="Security Tip"
        explanation="Always verify the recipient before sending money. If you recognize this transaction, you can proceed with caution."
        showExplanation={true}
      />
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
  transactionCard: {
    marginBottom: SPACING.lg,
    padding: SPACING.lg,
  },
  transactionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  transactionTitle: {
    ...TYPOGRAPHY.h4,
    fontWeight: '600',
    color: COLORS.text,
    marginLeft: SPACING.sm,
  },
  transactionDetails: {
    gap: SPACING.sm,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
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
  riskLevelContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.lg,
  },
  riskLevelLabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginRight: SPACING.sm,
  },
  decisionCard: {
    marginBottom: SPACING.lg,
    padding: SPACING.lg,
    alignItems: 'center',
  },
  decisionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  decisionTitle: {
    ...TYPOGRAPHY.h3,
    fontWeight: '600',
    color: COLORS.danger,
    marginLeft: SPACING.sm,
  },
  decisionMessage: {
    ...TYPOGRAPHY.body,
    color: COLORS.text,
    textAlign: 'center',
    marginBottom: SPACING.sm,
  },
  decisionExplanation: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    textAlign: 'center',
  },
  timelineCard: {
    marginBottom: SPACING.lg,
    padding: SPACING.lg,
  },
  timeline: {
    gap: SPACING.md,
  },
  timelineItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  timelineDot: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
    marginTop: 2,
  },
  timelineContent: {
    flex: 1,
  },
  timelineTime: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  timelineEvent: {
    ...TYPOGRAPHY.body,
    color: COLORS.text,
    fontWeight: '600',
  },
  signalsCard: {
    marginBottom: SPACING.lg,
    padding: SPACING.lg,
  },
  signalsList: {
    gap: SPACING.sm,
  },
  signalItem: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.md,
    ...SHADOWS.small,
  },
  signalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: SPACING.md,
  },
  signalIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  signalInfo: {
    flex: 1,
  },
  signalName: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.text,
  },
  signalDescription: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
  },
  signalDetails: {
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    padding: SPACING.md,
    paddingTop: SPACING.sm,
  },
  signalExplanation: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  signalMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  signalTime: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
  },
  signalPriority: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    fontWeight: '600',
  },
  actionButtons: {
    gap: SPACING.sm,
    marginBottom: SPACING.md,
  },
  proceedButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.warning,
    padding: SPACING.lg,
    borderRadius: BORDER_RADIUS.lg,
  },
  proceedButtonText: {
    ...TYPOGRAPHY.button,
    color: COLORS.textOnDark,
    marginLeft: SPACING.sm,
  },
  supportButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    padding: SPACING.lg,
    borderRadius: BORDER_RADIUS.lg,
  },
  supportButtonText: {
    ...TYPOGRAPHY.button,
    color: COLORS.textOnDark,
    marginLeft: SPACING.sm,
  },
});

export default SecurityReviewScreen;