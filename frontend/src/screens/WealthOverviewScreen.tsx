// src/screens/WealthOverviewScreen.tsx
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, FlatList } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import Card from '../components/common/Card';
import RiskBadge from '../components/common/RiskBadge';

const WealthOverviewScreen = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'recommendations' | 'goals'>('overview');

  // Mock wealth data
  const wealthData = {
    netWorth: 542500,
    totalAssets: 650000,
    totalLiabilities: 107500,
    cashFlow: {
      income: 75000,
      expenses: 26250,
      savings: 48750,
    },
  };

  const investmentAccounts = [
    { id: '1', name: 'Savings Account', balance: 48750, type: 'Savings', growth: '+2.4%' },
    { id: '2', name: 'Fixed Deposit', balance: 150000, type: 'FD', growth: '+7.5%' },
    { id: '3', name: 'Mutual Funds', balance: 250000, type: 'MF', growth: '+12.3%' },
    { id: '4', name: 'Retirement Fund', balance: 192500, type: 'RF', growth: '+8.7%' },
  ];

  const recommendations = [
    { 
      id: '1', 
      title: 'Emergency Fund', 
      description: 'Build ₹1,50,000 emergency fund to cover 6 months of expenses', 
      priority: 'HIGH' as const,
      confidence: 94,
      benefit: 'Avoid debt in emergencies',
      reason: 'Your liquid savings cover only 1.2 months of expenses'
    },
    { 
      id: '2', 
      title: 'SIP Investment', 
      description: 'Start ₹5,000 monthly SIP in index funds for long-term growth', 
      priority: 'MEDIUM' as const,
      confidence: 87,
      benefit: 'Expected 12% annual returns',
      reason: 'Your risk profile matches equity investment opportunities'
    },
    { 
      id: '3', 
      title: 'Insurance Review', 
      description: 'Review life insurance coverage adequacy', 
      priority: 'LOW' as const,
      confidence: 78,
      benefit: 'Ensure family financial security',
      reason: 'Coverage amount is 2x your annual income (recommended: 10x)'
    },
    { 
      id: '4', 
      title: 'Tax Planning', 
      description: 'Plan investments for tax benefits under Section 80C', 
      priority: 'MEDIUM' as const,
      confidence: 82,
      benefit: 'Save up to ₹1,50,000 in taxes',
      reason: 'Tax season approaches in 3 months'
    },
  ];

  const goals = [
    { id: '1', name: 'House Down Payment', target: 1500000, current: 350000, progress: 23 },
    { id: '2', name: 'Child Education', target: 1000000, current: 150000, progress: 15 },
    { id: '3', name: 'Retirement', target: 20000000, current: 250000, progress: 1.25 },
  ];

  const renderAccountItem = ({ item }: any) => (
    <Card style={styles.accountItem}>
      <View style={styles.accountHeader}>
        <View>
          <Text style={styles.accountName}>{item.name}</Text>
          <Text style={styles.accountType}>{item.type}</Text>
        </View>
        <Text style={styles.accountBalance}>₹{item.balance.toLocaleString()}</Text>
      </View>
      <View style={styles.accountFooter}>
        <Text style={styles.accountGrowth}>{item.growth}</Text>
        <TouchableOpacity>
          <Text style={styles.manageText}>Manage</Text>
        </TouchableOpacity>
      </View>
    </Card>
  );

  const renderRecommendationItem = ({ item }: any) => (
    <Card style={styles.recommendationItem}>
      <View style={styles.recommendationHeader}>
        <Text style={styles.recommendationTitle}>{item.title}</Text>
        <RiskBadge level={item.priority} showIcon={true} size="sm" />
      </View>
      <Text style={styles.recommendationDescription}>{item.description}</Text>
      
      <View style={styles.recommendationMeta}>
        <View style={styles.metaItem}>
          <Feather name="bar-chart-2" size={14} color={COLORS.textSecondary} />
          <Text style={styles.metaText}>Confidence: {item.confidence}%</Text>
        </View>
        <View style={styles.metaItem}>
          <Feather name="target" size={14} color={COLORS.textSecondary} />
          <Text style={styles.metaText}>Benefit: {item.benefit}</Text>
        </View>
      </View>
      
      <View style={styles.reasonContainer}>
        <Text style={styles.reasonLabel}>Why this recommendation?</Text>
        <Text style={styles.reasonText}>{item.reason}</Text>
      </View>
      
      <TouchableOpacity style={styles.actionButton}>
        <Text style={styles.actionButtonText}>Take Action</Text>
      </TouchableOpacity>
    </Card>
  );

  const renderGoalItem = ({ item }: any) => (
    <Card style={styles.goalItem}>
      <View style={styles.goalHeader}>
        <Text style={styles.goalName}>{item.name}</Text>
        <Text style={styles.goalProgress}>{item.progress}%</Text>
      </View>
      <View style={styles.progressBar}>
        <View 
          style={[
            styles.progressFill, 
            { width: `${Math.min(item.progress, 100)}%`, backgroundColor: COLORS.primary }
          ]} 
        />
      </View>
      <View style={styles.goalValues}>
        <Text style={styles.goalValue}>₹{item.current.toLocaleString()}</Text>
        <Text style={styles.goalTarget}>of ₹{item.target.toLocaleString()}</Text>
      </View>
    </Card>
  );

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity>
          <Feather name="arrow-left" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Wealth Overview</Text>
        <TouchableOpacity>
          <Feather name="more-vertical" size={24} color={COLORS.text} />
        </TouchableOpacity>
      </View>

      {/* Wealth Summary */}
      <Card style={styles.summaryCard}>
        <Text style={styles.summaryTitle}>Net Worth</Text>
        <Text style={styles.netWorth}>₹{wealthData.netWorth.toLocaleString()}</Text>
        <View style={styles.statsContainer}>
          <View style={styles.statColumn}>
            <Text style={styles.statLabel}>Assets</Text>
            <Text style={styles.statValue}>₹{wealthData.totalAssets.toLocaleString()}</Text>
          </View>
          <View style={styles.statColumn}>
            <Text style={styles.statLabel}>Liabilities</Text>
            <Text style={styles.statValue}>₹{wealthData.totalLiabilities.toLocaleString()}</Text>
          </View>
        </View>
      </Card>

      {/* Cash Flow */}
      <Card style={styles.cashFlowCard}>
        <Text style={styles.cashFlowTitle}>Monthly Cash Flow</Text>
        <View style={styles.cashFlowItems}>
          <View style={styles.cashFlowItem}>
            <Text style={styles.incomeLabel}>Income</Text>
            <Text style={styles.incomeValue}>₹{wealthData.cashFlow.income.toLocaleString()}</Text>
          </View>
          <View style={styles.cashFlowItem}>
            <Text style={styles.expenseLabel}>Expenses</Text>
            <Text style={styles.expenseValue}>₹{wealthData.cashFlow.expenses.toLocaleString()}</Text>
          </View>
          <View style={styles.cashFlowItem}>
            <Text style={styles.savingsLabel}>Savings</Text>
            <Text style={styles.savingsValue}>₹{wealthData.cashFlow.savings.toLocaleString()}</Text>
          </View>
        </View>
      </Card>

      {/* Tabs */}
      <View style={styles.tabsContainer}>
        <TouchableOpacity 
          style={[styles.tab, activeTab === 'overview' && styles.activeTab]}
          onPress={() => setActiveTab('overview')}
        >
          <Feather name="pie-chart" size={20} color={activeTab === 'overview' ? COLORS.primary : COLORS.textSecondary} />
          <Text style={[styles.tabText, activeTab === 'overview' && styles.activeTabText]}>Overview</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.tab, activeTab === 'recommendations' && styles.activeTab]}
          onPress={() => setActiveTab('recommendations')}
        >
          <Feather name="lightbulb" size={20} color={activeTab === 'recommendations' ? COLORS.primary : COLORS.textSecondary} />
          <Text style={[styles.tabText, activeTab === 'recommendations' && styles.activeTabText]}>Recommendations</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.tab, activeTab === 'goals' && styles.activeTab]}
          onPress={() => setActiveTab('goals')}
        >
          <Feather name="target" size={20} color={activeTab === 'goals' ? COLORS.primary : COLORS.textSecondary} />
          <Text style={[styles.tabText, activeTab === 'goals' && styles.activeTabText]}>Goals</Text>
        </TouchableOpacity>
      </View>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <View style={styles.tabContent}>
          <Text style={styles.sectionTitle}>Investment Accounts</Text>
          <FlatList
            data={investmentAccounts}
            renderItem={renderAccountItem}
            keyExtractor={(item) => item.id}
            showsVerticalScrollIndicator={false}
          />
        </View>
      )}

      {activeTab === 'recommendations' && (
        <View style={styles.tabContent}>
          <Text style={styles.sectionTitle}>Personalized Recommendations</Text>
          <FlatList
            data={recommendations}
            renderItem={renderRecommendationItem}
            keyExtractor={(item) => item.id}
            showsVerticalScrollIndicator={false}
          />
        </View>
      )}

      {activeTab === 'goals' && (
        <View style={styles.tabContent}>
          <Text style={styles.sectionTitle}>Financial Goals</Text>
          <FlatList
            data={goals}
            renderItem={renderGoalItem}
            keyExtractor={(item) => item.id}
            showsVerticalScrollIndicator={false}
          />
        </View>
      )}

      {/* Wealth Insights */}
      <Card style={styles.insightsCard}>
        <View style={styles.insightsHeader}>
          <Feather name="trending-up" size={20} color={COLORS.success} />
          <Text style={styles.insightsTitle}>Wealth Insights</Text>
        </View>
        <Text style={styles.insightsText}>Your financial health is improving! Your monthly savings have increased by 15% compared to last quarter.</Text>
        <TouchableOpacity style={styles.insightsButton}>
          <Text style={styles.insightsButtonText}>View Full Analysis</Text>
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
  summaryCard: {
    marginBottom: SPACING.lg,
    padding: SPACING.lg,
  },
  summaryTitle: {
    ...TYPOGRAPHY.body,
    color: COLORS.textSecondary,
    marginBottom: SPACING.sm,
  },
  netWorth: {
    ...TYPOGRAPHY.h2,
    fontWeight: '700',
    color: COLORS.primary,
    marginBottom: SPACING.md,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statColumn: {
    alignItems: 'center',
  },
  statLabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
  },
  statValue: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: SPACING.xs,
  },
  cashFlowCard: {
    marginBottom: SPACING.lg,
    padding: SPACING.lg,
  },
  cashFlowTitle: {
    ...TYPOGRAPHY.h4,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  cashFlowItems: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  cashFlowItem: {
    alignItems: 'center',
  },
  incomeLabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
  },
  incomeValue: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.success,
    marginTop: SPACING.xs,
  },
  expenseLabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
  },
  expenseValue: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.danger,
    marginTop: SPACING.xs,
  },
  savingsLabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
  },
  savingsValue: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.primary,
    marginTop: SPACING.xs,
  },
  tabsContainer: {
    flexDirection: 'row',
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    marginBottom: SPACING.lg,
    ...SHADOWS.small,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.lg,
  },
  activeTab: {
    backgroundColor: COLORS.primaryLight,
  },
  tabText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginTop: SPACING.xs,
  },
  activeTabText: {
    color: COLORS.primary,
    fontWeight: '600',
  },
  tabContent: {
    marginBottom: SPACING.lg,
  },
  sectionTitle: {
    ...TYPOGRAPHY.h4,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  accountItem: {
    padding: SPACING.md,
    marginBottom: SPACING.sm,
  },
  accountHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.xs,
  },
  accountName: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.text,
  },
  accountType: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
  },
  accountBalance: {
    ...TYPOGRAPHY.body,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  accountFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  accountGrowth: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.success,
    fontWeight: '600',
  },
  manageText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.primary,
    fontWeight: '600',
  },
  recommendationItem: {
    padding: SPACING.md,
    marginBottom: SPACING.sm,
  },
  recommendationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  recommendationTitle: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.text,
  },
  recommendationDescription: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginBottom: SPACING.sm,
  },
  recommendationMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: SPACING.sm,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  metaText: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textSecondary,
    marginLeft: SPACING.xs,
  },
  reasonContainer: {
    marginBottom: SPACING.sm,
  },
  reasonLabel: {
    ...TYPOGRAPHY.caption,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.xs,
  },
  reasonText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
  },
  actionButton: {
    backgroundColor: COLORS.primary,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    alignItems: 'center',
  },
  actionButtonText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.surface,
    fontWeight: '600',
  },
  goalItem: {
    padding: SPACING.md,
    marginBottom: SPACING.sm,
  },
  goalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  goalName: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.text,
  },
  goalProgress: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.primary,
  },
  progressBar: {
    height: 8,
    backgroundColor: COLORS.border,
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: SPACING.sm,
  },
  progressFill: {
    height: '100%',
  },
  goalValues: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  goalValue: {
    ...TYPOGRAPHY.bodySm,
    fontWeight: '600',
    color: COLORS.text,
  },
  goalTarget: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
  },
  insightsCard: {
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

export default WealthOverviewScreen;