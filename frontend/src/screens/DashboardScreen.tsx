// src/screens/DashboardScreen.tsx
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, FlatList, Dimensions } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import GlassCard from '../components/common/GlassCard';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { TYPOGRAPHY, SPACING, BORDER_RADIUS } from '../constants/theme';

const DashboardScreen = () => {
  const insets = useSafeAreaInsets();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const quickActions = [
    { id: '1', title: 'Transfer Money', icon: 'send', color: COLORS.primary },
    { id: '2', title: 'Check Balance', icon: 'pie-chart', color: COLORS.success },
    { id: '3', title: 'View Statements', icon: 'file-text', color: COLORS.warning },
    { id: '4', title: 'Security Check', icon: 'shield', color: COLORS.s_danger },
  ];

  const recentTransactions = [
    { id: '1', description: 'Grocery Purchase', amount: -2450, date: 'Today', category: 'Shopping' },
    { id: '2', description: 'Salary Credit', amount: 50000, date: 'Yesterday', category: 'Income' },
    { id: '3', description: 'Electricity Bill', amount: -1200, date: 'Jun 8', category: 'Utilities' },
  ];

  const renderTransactionItem = ({ item }: any) => (
    <View style={styles.transactionItem}>
      <View style={styles.transactionContent}>
        <View>
          <Text style={styles.transactionDescription}>{item.description}</Text>
          <Text style={styles.transactionCategory}>{item.category}</Text>₹
        </View>
        <Text style={[
          styles.transactionAmount,
          { color: item.amount > 0 ? COLORS.success : COLORS.s_danger }
        ]}>
          {item.amount > 0 ? '+' : '-'}₹{Math.abs(item.amount).toLocaleString()}
        </Text>
      </View>
      <Text style={styles.transactionDate}>{item.date}</Text>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Sidebar Drawer */}
      {isDrawerOpen && (
        <View style={styles.drawerOverlay} onTouchStart={() => setIsDrawerOpen(false)} />
      )}
      <View style={[styles.drawer, isDrawerOpen && styles.drawerOpen]}>
        <View style={styles.drawerHeader}>
          <Feather name="user" size={32} color={COLORS.textOnDark} />
          <Text style={styles.drawerTitle}>Swayam Kohli</Text>
          <TouchableOpacity onPress={() => setIsDrawerOpen(false)}>
            <Feather name="x" size={24} color={COLORS.textOnDark} />
          </TouchableOpacity>
        </View>
        <View style={styles.drawerItems}>
          {[
            { label: 'Home', icon: 'home', active: true },
            { label: 'Wealth', icon: 'pie-chart', active: false },
            { label: 'Security', icon: 'shield', active: false },
            { label: 'Profile', icon: 'user', active: false },
            { label: 'Settings', icon: 'settings', active: false },
          ].map((item) => (
            <TouchableOpacity key={item.label} style={styles.drawerItem}>
              <Feather name={item.icon} size={20} color={item.active ? COLORS.accent : COLORS.textOnDark} />
              <Text style={[styles.drawerItemLabel, item.active && styles.drawerItemLabelActive]}>
                {item.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Main Content */}
      <ScrollView 
        style={styles.content}
        contentContainerStyle={[
          styles.contentContainer,
          {
            paddingTop: insets.top, // ✅ Flush-top header (no extra padding)
            paddingBottom: insets.bottom + SPACING.xxl,
          }
        ]}
        showsVerticalScrollIndicator={false}
        bounces={true}
      >
        {/* Top header bar — now flush to top */}
        <View style={styles.headerBar}>
          <TouchableOpacity onPress={() => setIsDrawerOpen(true)}>
            <Feather name="menu" size={24} color={COLORS.textOnDark} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>SecureWealth Twin</Text>
          <TouchableOpacity>
            <Feather name="bell" size={24} color={COLORS.textOnDark} />
          </TouchableOpacity>
        </View>

        <View style={styles.mainContent}>
          {/* Greeting & Balance */}
          <View style={styles.greetingSection}>
            <Text style={styles.greeting}>Good morning, Swayam!</Text>
            <Text style={styles.accountLabel}>Available Balance</Text>
            <Text style={styles.balance}>₹48,750.00</Text>
          </View>

          {/* Security Status — FIXED SHADING, GOLD VISIBLE */}
          <GlassCard style={styles.securityCard}>
            <View style={styles.securityHeader}>
              <Feather name="shield" size={20} color={COLORS.primary} />
              <Text style={styles.securityTitle}>Security Status</Text>
            </View>
            <View style={styles.securityStats}>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>98%</Text>
                <Text style={styles.statLabel}>Protection</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>0</Text>
                <Text style={styles.statLabel}>Threats</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>Active</Text>
                <Text style={styles.statLabel}>Monitoring</Text>
              </View>
            </View>
          </GlassCard>

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
          <GlassCard style={styles.insightsCard}>
            <View style={styles.insightsHeader}>
              <Feather name="trending-up" size={20} color={COLORS.success} />
              <Text style={styles.insightsTitle}>Wealth Insights</Text>
            </View>
            <Text style={styles.insightsText}>Your financial health is improving!</Text>
            <TouchableOpacity style={styles.insightsButton}>
              <Text style={styles.insightsButtonText}>View Analysis</Text>
            </TouchableOpacity>
          </GlassCard>
        </View>
      </ScrollView>
    </View>
  );
};

const { width } = Dimensions.get('window');

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background, // ✅ #F5F9FA — perfect bank-grade light
  },
  drawerOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.5)',
    zIndex: 100,
  },
  drawer: {
    position: 'absolute',
    top: 0,
    left: -width,
    height: '100%',
    width: width * 0.8,
    backgroundColor: COLORS.primaryDark,
    zIndex: 200,
    paddingTop: 48,
    transitionProperty: 'left',
    transitionDuration: '300ms',
  },
  drawerOpen: {
    left: 0,
  },
  drawerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
    paddingBottom: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  drawerTitle: {
    flex: 1,
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.textOnDark,
    marginLeft: SPACING.sm,
  },
  drawerItems: {
    padding: SPACING.lg,
  },
  drawerItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.sm,
    marginBottom: SPACING.xs,
  },
  drawerItemLabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textOnDark,
    marginLeft: SPACING.sm,
  },
  drawerItemLabelActive: {
    color: COLORS.accent, // ✅ Rich gold #D4AF37 — highly visible
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: SPACING.lg,
  },
  headerBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.sm, // ✅ Reduced padding → flush-top
    backgroundColor: COLORS.primaryDark,
  },
  headerTitle: {
    ...TYPOGRAPHY.h4,
    fontWeight: '600',
    color: COLORS.textOnDark,
  },
  mainContent: {
    flex: 1,
  },
  greetingSection: {
    marginBottom: SPACING.xl,
    paddingTop: SPACING.md,
  },
  greeting: {
    ...TYPOGRAPHY.h3,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  accountLabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginBottom: SPACING.xs,
  },
  balance: {
    ...TYPOGRAPHY.h1,
    fontWeight: '700',
    color: COLORS.accent, // ✅ Rich gold #D4AF37 — now clearly visible
  },
  securityCard: {
    marginBottom: SPACING.lg,
    backgroundColor: 'rgba(255, 255, 255, 0.7)',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.04)',
    borderRadius: BORDER_RADIUS.lg,
  },
  securityHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  securityTitle: {
    ...TYPOGRAPHY.h4,
    fontWeight: '600',
    marginLeft: SPACING.sm,
    color: COLORS.text,
  },
  securityStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    ...TYPOGRAPHY.h3,
    fontWeight: '700',
    color: COLORS.primary, // Green — strong, clear
  },
  statLabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginTop: SPACING.xs,
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
    borderWidth: 1,
    borderColor: COLORS.border,
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
    color: COLORS.accent, // ✅ Rich gold — now visible
    fontWeight: '600',
  },
  transactionItem: {
    backgroundColor: COLORS.surface,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    marginBottom: SPACING.sm,
    borderWidth: 1,
    borderColor: COLORS.border,
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
    backgroundColor: 'rgba(255, 255, 255, 0.7)',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.04)',
    borderRadius: BORDER_RADIUS.lg,
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
    marginLeft: SPACING.sm,
    color: COLORS.text,
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