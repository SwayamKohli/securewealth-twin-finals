// src/screens/DashboardScreen.tsx
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, FlatList, RefreshControl } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import Card from '../components/common/Card';
import RiskBadge from '../components/common/RiskBadge';
import ExplainableAlert from '../components/common/ExplainableAlert';

const DashboardScreen = () => {
  const [refreshing, setRefreshing] = useState(false);

  // Mock data
  const quickActions = [
    { id: '1', title: 'Fund Transfer', icon: 'send', color: COLORS.primary },
    { id: '2', title: 'UPI Pay', icon: 'zap', color: COLORS.accent },
    { id: '3', title: 'View Statements', icon: 'file-text', color: COLORS.info },
    { id: '4', title: 'Security Check', icon: 'shield', color: COLORS.danger },
  ];

  const recentTransactions = [
    { id: '1', description: 'Grocery Purchase', amount: -2450, date: 'Today', category: 'Shopping', status: 'SUCCESS' },
    { id: '2', description: 'Salary Credit', amount: 50000, date: 'Yesterday', category: 'Income', status: 'SUCCESS' },
    { id: '3', description: 'Electricity Bill', amount: -1200, date: 'Jun 8', category: 'Utilities', status: 'SUCCESS' },
    { id: '4', description: 'Investment Return', amount: 2500, date: 'Jun 7', category: 'Investment', status: 'SUCCESS' },
  ];

  const securityStatus = {
    level: 'LOW' as const,
    score: 12,
    signals: [
      { type: 'DEVICE', status: 'TRUSTED', description: 'iPhone 14, Delhi' },
      { type: 'TIME', status: 'NORMAL', description: 'Daytime activity' },
      { type: 'BEHAVIOR', status: 'NORMAL', description: 'Regular spending pattern' },
    ]
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    setRefreshing(false);
  };

  const renderTransactionItem = ({ item }: any) => (
    <TouchableOpacity style={styles.transactionItem}>
      <View style={styles.transactionContent}>
        <View>
          <Text style={styles.transactionDescription}>{item.description}</Text>
          <Text style={styles.transactionCategory}>{item.category}</Text>
        </View>
        <Text style={[
          styles.transactionAmount,
          { color: item.amount > 0 ? COLORS.success : COLORS.danger }
        ]}>
          {item.amount > 0 ? '+' : ''}₹{Math.abs(item.amount).toLocaleString()}
        </Text>
      </View>
      <Text style={styles.transactionDate}>{item.date}</Text>
    </TouchableOpacity>
  );

  return (
    <ScrollView 
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} tintColor={COLORS.primary} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.greeting}>Good morning, Swayam!</Text>
        <Text style={styles.lastLogin}>Last login: Today, 09:15 AM</Text>
      </View>

      {/* Net Worth Card */}
      <Card style={styles.netWorthCard}>
        <View style={styles.netWorthHeader}>
          <Text style={styles.netWorthLabel}>Available Balance</Text>
          <TouchableOpacity>
            <Feather name="refresh-cw" size={20} color={COLORS.textSecondary} />
          </TouchableOpacity>
        </View>
        <Text style={styles.balance}>₹48,750.00</Text>
        <View style={styles.netWorthDetails}>
          <View style={styles.detailItem}>
            <Text style={styles.detailValue}>₹52,000</Text>
            <Text style={styles.detailLabel}>Total Assets</Text>
          </View>
          <View style={styles.detailItem}>
            <Text style={styles.detailValue}>₹3,250</Text>
            <Text style={styles.detailLabel}>Total Liabilities</Text>
          </View>
          <View style={styles.detailItem}>
            <Text style={styles.detailValue}>₹48,750</Text>
            <Text style={styles.detailLabel}>Net Worth</Text>
          </View>
        </View>
      </Card>

      {/* Security Status Card */}
      <Card style={styles.securityCard}>
        <View style={styles.securityHeader}>
          <Feather name="shield" size={20} color={COLORS.primary} />
          <Text style={styles.securityTitle}>Security Status</Text>
          <RiskBadge level={securityStatus.level} showIcon={false} size="sm" />
        </View>
        
        <View style={styles.securityStats}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>98%</Text>
            <Text style={styles.statLabel}>Protection</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>0</Text>
            <Text style={styles.statLabel}>Active Threats</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>Active</Text>
            <Text style={styles.statLabel}>Monitoring</Text>
          </View>
        </View>

        {/* Security Signals */}
        <View style={styles.securitySignals}>
          {securityStatus.signals.map((signal, index) => (
            <View key={index} style={styles.signalItem}>
              <Feather 
                name={signal.status === 'TRUSTED' || signal.status === 'NORMAL' ? 'check-circle' : 'alert-circle'} 
                size={16} 
                color={signal.status === 'TRUSTED' || signal.status === 'NORMAL' ? COLORS.success : COLORS.warning} 
              />
              <Text style={styles.signalText}>{signal.description}</Text>
            </View>
          ))}
        </View>
      </Card>

      {/* Quick Actions */}
      <View style={styles.actionsContainer}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.actionsGrid}>
          {quickActions.map((action) => (
            <TouchableOpacity key={action.id} style={styles.actionItem}>
              <View style={[styles.actionIcon, { backgroundColor: action.color + '10' }]}>
                <Feather name={action.icon as any} size={24} color={action.color} />
              </View>
              <Text style={styles.actionTitle}>{action.title}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Recent Transactions */}
      <View style={styles.transactionsContainer}>
        <View style={styles.transactionsHeader}>
          <Text style={styles.sectionTitle}>Recent Transactions</Text>
          <TouchableOpacity>
            <Text style={styles.viewAllText}>View All</Text>
          </TouchableOpacity>
        </View>
        <FlatList
          data={recentTransactions}
          renderItem={renderTransactionItem}
          keyExtractor={(item) => item.id}
          showsVerticalScrollIndicator={false}
          scrollEnabled={false}
        />
      </View>

      {/* Wealth Insights */}
      <Card style={styles.insightsCard}>
        <View style={styles.insightsHeader}>
          <Feather name="trending-up" size={20} color={COLORS.success} />
          <Text style={styles.insightsTitle}>Wealth Insights</Text>
        </View>
        <Text style={styles.insightsText}>Your financial health is improving! Your monthly savings have increased by 15% compared to last month.</Text>
        <TouchableOpacity style={styles.insightsButton}>
          <Text style={styles.insightsButtonText}>View Full Analysis</Text>
        </TouchableOpacity>
      </Card>

      {/* Trusted Devices Alert */}
      <ExplainableAlert
        type="info"
        title="Trusted Devices"
        explanation="This device is registered as trusted. You can manage your trusted devices from the security settings."
        actionText="Manage Devices"
        onAction={() => console.log('Manage devices pressed')}
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
    marginBottom: SPACING.xl,
  },
  greeting: {
    ...TYPOGRAPHY.h3,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.xs,
  },
  lastLogin: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
  },
  netWorthCard: {
    marginBottom: SPACING.lg,
    padding: SPACING.lg,
  },
  netWorthHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  netWorthLabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
  },
  balance: {
    ...TYPOGRAPHY.h1,
    fontWeight: '700',
    color: COLORS.accent,
    marginBottom: SPACING.md,
  },
  netWorthDetails: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    paddingTop: SPACING.md,
  },
  detailItem: {
    alignItems: 'center',
  },
  detailValue: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.text,
  },
  detailLabel: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textSecondary,
    marginTop: SPACING.xs,
  },
  securityCard: {
    marginBottom: SPACING.lg,
    padding: SPACING.lg,
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
    flex: 1,
  },
  securityStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: SPACING.md,
  },
  statItem: {
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
  securitySignals: {
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    paddingTop: SPACING.md,
  },
  signalItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  signalText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginLeft: SPACING.sm,
  },
  actionsContainer: {
    marginBottom: SPACING.lg,
  },
  sectionTitle: {
    ...TYPOGRAPHY.h4,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  actionsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
  },
  actionItem: {
    width: '48%',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    padding: SPACING.lg,
    borderRadius: BORDER_RADIUS.lg,
    marginBottom: SPACING.md,
    ...SHADOWS.small,
  },
  actionIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  actionTitle: {
    ...TYPOGRAPHY.bodySm,
    fontWeight: '600',
    color: COLORS.text,
    textAlign: 'center',
  },
  transactionsContainer: {
    marginBottom: SPACING.lg,
  },
  transactionsHeader: {
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
  transactionItem: {
    backgroundColor: COLORS.surface,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    marginBottom: SPACING.sm,
    ...SHADOWS.small,
  },
  transactionContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.xs,
  },
  transactionDescription: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.text,
  },
  transactionCategory: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
  },
  transactionAmount: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
  },
  transactionDate: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textSecondary,
  },
  insightsCard: {
    marginBottom: SPACING.lg,
    padding: SPACING.lg,
  },
  insightsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  insightsTitle: {
    ...TYPOGRAPHY.h4,
    fontWeight: '600',
    color: COLORS.text,
    marginLeft: SPACING.sm,
  },
  insightsText: {
    ...TYPOGRAPHY.body,
    color: COLORS.textSecondary,
    marginBottom: SPACING.md,
  },
  insightsButton: {
    backgroundColor: COLORS.primary,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    alignItems: 'center',
  },
  insightsButtonText: {
    ...TYPOGRAPHY.body,
    color: COLORS.surface,
    fontWeight: '600',
  },
});

export default DashboardScreen;