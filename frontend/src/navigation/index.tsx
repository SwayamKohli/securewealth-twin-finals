// src/navigation/index.tsx
// SecureWealth Twin — Navigation Architecture
//
// Structure:
//   AppNavigator
//   ├── AuthScreen (not logged in)
//   └── RootNavigator (logged in)
//       ├── MainTabs (Bottom Tab Navigator)
//       │   ├── Tab: Home
//       │   │   └── HomeStack
//       │   │       └── DashboardScreen
//       │   ├── Tab: Send Money
//       │   │   └── SendStack
//       │   │       ├── TransactionInitiateScreen
//       │   │       ├── SecurityReviewScreen
//       │   │       └── TransactionResultScreen
//       │   ├── Tab: My Wealth
//       │   │   └── WealthStack
//       │   │       └── WealthOverviewScreen
//       │   ├── Tab: Safety
//       │   │   └── SafetyStack
//       │   │       ├── SafetyHubScreen
//       │   │       ├── PhishingScannerScreen
//       │   │       └── MySecurityActivityScreen
//       │   └── Tab: Profile
//       │       └── ProfileStack
//       │           └── ProfileScreen (placeholder)
//       └── AuditModal (Modal — admin only, from Profile)
//           └── AuditDashboardScreen

import React, { useState, useCallback } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Feather } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { COLORS } from '../constants/colors';
import { TYPOGRAPHY, SPACING, BORDER_RADIUS, SHADOWS, TAB_BAR, ANIMATION } from '../constants/theme';

// ── Screens ──────────────────────────────────────────────────────────────────
import AuthScreen from '../screens/AuthScreen';
import DashboardScreen from '../screens/DashboardScreen';
import TransactionInitiateScreen from '../screens/TransactionInitiateScreen';
import SecurityReviewScreen from '../screens/SecurityReviewScreen';
import TransactionResultScreen from '../screens/TransactionResultScreen';
import WealthOverviewScreen from '../screens/WealthOverviewScreen';
import SafetyHubScreen from '../screens/SafetyHubScreen';
import PhishingScannerScreen from '../screens/PhishingScannerScreen';
import MySecurityActivityScreen from '../screens/MySecurityActivityScreen';
import AuditDashboardScreen from '../screens/AuditDashboardScreen';

// ── Navigator instances ──────────────────────────────────────────────────────
const RootStack = createStackNavigator();
const Tab = createBottomTabNavigator();
const HomeStack = createStackNavigator();
const SendStack = createStackNavigator();
const WealthStack = createStackNavigator();
const SafetyStack = createStackNavigator();
const ProfileStack = createStackNavigator();

// ── Shared header options ────────────────────────────────────────────────────
// Used by all stack screens (drill-down pages inside tabs)
const sharedStackScreenOptions = {
  headerStyle: {
    backgroundColor: COLORS.surface,
    elevation: 0,
    shadowOpacity: 0,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  headerTintColor: COLORS.primary,
  headerTitleStyle: {
    ...TYPOGRAPHY.h4,
    color: COLORS.text,
  },
  headerBackTitleVisible: false,
  cardStyle: {
    backgroundColor: COLORS.background,
  },
  // Subtle slide animation for drill-down screens
  transitionSpec: {
    open: {
      animation: 'timing' as const,
      config: { duration: ANIMATION.normal },
    },
    close: {
      animation: 'timing' as const,
      config: { duration: ANIMATION.fast },
    },
  },
};

// ── Tab 1: Home Stack ────────────────────────────────────────────────────────
const HomeStackNavigator = ({ handleLogout }: { handleLogout: () => void }) => (
  <HomeStack.Navigator screenOptions={sharedStackScreenOptions}>
    <HomeStack.Screen
      name="Dashboard"
      component={DashboardScreen}
      options={({ navigation }: any) => ({
        // Dashboard gets the branded green header
        headerStyle: {
          backgroundColor: COLORS.primaryDark,
          elevation: 0,
          shadowOpacity: 0,
        },
        headerTintColor: COLORS.textOnDark,
        headerTitleStyle: {
          ...TYPOGRAPHY.h4,
          color: COLORS.textOnDark,
          fontWeight: '700',
        },
        title: 'SecureWealth',
        headerRight: () => (
          <View style={styles.headerActions}>
            <TouchableOpacity
              style={styles.headerIconBtn}
              onPress={() => navigation.navigate('Notifications')}
              activeOpacity={0.7}
            >
              <Feather name="bell" size={22} color={COLORS.textOnDark} />
              {/* Notification dot */}
              <View style={styles.notifDot} />
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.headerIconBtn, { marginLeft: SPACING.sm }]}
              onPress={handleLogout}
              activeOpacity={0.7}
            >
              <Feather name="log-out" size={20} color={COLORS.textOnDark} />
            </TouchableOpacity>
          </View>
        ),
      })}
    />
  </HomeStack.Navigator>
);

// ── Tab 2: Send Money Stack ──────────────────────────────────────────────────
const SendStackNavigator = () => (
  <SendStack.Navigator screenOptions={sharedStackScreenOptions}>
    <SendStack.Screen
      name="TransactionInitiate"
      component={TransactionInitiateScreen}
      options={{ title: 'Send Money' }}
    />
    <SendStack.Screen
      name="SecurityReview"
      component={SecurityReviewScreen}
      options={{
        title: 'Security Check',
        // Prevent going back mid-review (security flow)
        headerLeft: () => null,
        gestureEnabled: false,
      }}
    />
    <SendStack.Screen
      name="TransactionResult"
      component={TransactionResultScreen}
      options={{
        title: 'Payment Status',
        // Prevent going back to result (flow is complete)
        headerLeft: () => null,
        gestureEnabled: false,
      }}
    />
  </SendStack.Navigator>
);

// ── Tab 3: My Wealth Stack ───────────────────────────────────────────────────
const WealthStackNavigator = () => (
  <WealthStack.Navigator screenOptions={sharedStackScreenOptions}>
    <WealthStack.Screen
      name="WealthOverview"
      component={WealthOverviewScreen}
      options={{
        title: 'My Wealth',
        headerStyle: {
          backgroundColor: COLORS.primaryDark,
          elevation: 0,
          shadowOpacity: 0,
        },
        headerTintColor: COLORS.textOnDark,
        headerTitleStyle: {
          ...TYPOGRAPHY.h4,
          color: COLORS.textOnDark,
          fontWeight: '700',
        },
      }}
    />
    {/* Future: DepositDetailScreen, LoanDetailScreen will be added here */}
  </WealthStack.Navigator>
);

// ── Tab 4: Safety Stack ──────────────────────────────────────────────────────
const SafetyStackNavigator = () => (
  <SafetyStack.Navigator screenOptions={sharedStackScreenOptions}>
    {/* SafetyHub is the landing screen for this tab — two action cards:
        "Check a Message" and "My Security Activity" (the latter is a
        placeholder until a future batch wires up audit_logs.json). */}
    <SafetyStack.Screen
      name="SafetyHub"
      component={SafetyHubScreen}
      options={{
        title: 'Safety',
        headerStyle: {
          backgroundColor: COLORS.primaryDark,
          elevation: 0,
          shadowOpacity: 0,
        },
        headerTintColor: COLORS.textOnDark,
        headerTitleStyle: {
          ...TYPOGRAPHY.h4,
          color: COLORS.textOnDark,
          fontWeight: '700',
        },
      }}
    />
    <SafetyStack.Screen
      name="PhishingScanner"
      component={PhishingScannerScreen}
      options={{ title: 'Check a Message' }}
    />
    <SafetyStack.Screen
      name="MySecurityActivity"
      component={MySecurityActivityScreen}
      options={{ title: 'My Security Activity' }}
    />
  </SafetyStack.Navigator>
);

// ── Tab 5: Profile Stack ─────────────────────────────────────────────────────
// Placeholder profile screen until ProfileScreen is built
const PlaceholderProfileScreen = ({ navigation }: any) => (
  <View style={styles.placeholder}>
    <Feather name="user" size={48} color={COLORS.textTertiary} />
    <Text style={styles.placeholderTitle}>My Profile</Text>
    <Text style={styles.placeholderSub}>Profile settings coming soon</Text>
    {/* Admin audit access — only shown here, not in user-facing tabs */}
    <TouchableOpacity
      style={styles.adminBtn}
      onPress={() => navigation.navigate('AuditModal')}
      activeOpacity={0.8}
    >
      <Feather name="shield" size={16} color={COLORS.textOnDark} />
      <Text style={styles.adminBtnText}>Admin: Audit Dashboard</Text>
    </TouchableOpacity>
  </View>
);

const ProfileStackNavigator = () => (
  <ProfileStack.Navigator screenOptions={sharedStackScreenOptions}>
    <ProfileStack.Screen
      name="Profile"
      component={PlaceholderProfileScreen}
      options={{ title: 'My Profile' }}
    />
    {/* Future: TrustedDevicesScreen, SecuritySettingsScreen */}
  </ProfileStack.Navigator>
);

// ── Custom Tab Bar ────────────────────────────────────────────────────────────
// Matches PSB's clean bottom nav with proper safe area handling
type TabBarProps = {
  state: any;
  descriptors: any;
  navigation: any;
};

const CustomTabBar = ({ state, descriptors, navigation }: TabBarProps) => {
  const insets = useSafeAreaInsets();

  const tabs = [
    { icon: 'home', label: 'Home' },
    { icon: 'send', label: 'Send' },
    { icon: 'trending-up', label: 'My Wealth' },
    { icon: 'shield', label: 'Safety' },
    { icon: 'user', label: 'Profile' },
  ] as const;

  return (
    <View
      style={[
        styles.tabBar,
        {
          paddingBottom: Math.max(insets.bottom, SPACING.sm),
          height: TAB_BAR.height + Math.max(insets.bottom, SPACING.sm),
        },
      ]}
    >
      {state.routes.map((route: any, index: number) => {
        const { options } = descriptors[route.key];
        const isFocused = state.index === index;
        const tab = tabs[index];

        const onPress = () => {
          const event = navigation.emit({
            type: 'tabPress',
            target: route.key,
            canPreventDefault: true,
          });
          if (!isFocused && !event.defaultPrevented) {
            navigation.navigate(route.name);
          }
        };

        return (
          <TouchableOpacity
            key={route.key}
            onPress={onPress}
            style={styles.tabItem}
            activeOpacity={0.7}
            accessibilityRole="button"
            accessibilityState={isFocused ? { selected: true } : {}}
            accessibilityLabel={options.tabBarAccessibilityLabel || tab.label}
          >
            {/* Active tab gets a green pill indicator above icon */}
            {isFocused && <View style={styles.tabActivePill} />}

            <Feather
              name={tab.icon as any}
              size={TAB_BAR.iconSize}
              color={isFocused ? COLORS.primary : COLORS.textTertiary}
            />
            <Text
              style={[
                styles.tabLabel,
                { color: isFocused ? COLORS.primary : COLORS.textTertiary },
              ]}
              numberOfLines={1}
            >
              {tab.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
};

// ── Bottom Tab Navigator ──────────────────────────────────────────────────────
const MainTabs = ({ handleLogout }: { handleLogout: () => void }) => (
  <Tab.Navigator
    tabBar={(props) => <CustomTabBar {...props} />}
    screenOptions={{ headerShown: false }}
  >
    <Tab.Screen name="HomeTab">
      {() => <HomeStackNavigator handleLogout={handleLogout} />}
    </Tab.Screen>
    <Tab.Screen name="SendTab" component={SendStackNavigator} />
    <Tab.Screen name="WealthTab" component={WealthStackNavigator} />
    <Tab.Screen name="SafetyTab" component={SafetyStackNavigator} />
    <Tab.Screen name="ProfileTab" component={ProfileStackNavigator} />
  </Tab.Navigator>
);

// ── Root Navigator (post-login) ───────────────────────────────────────────────
// Wraps tabs + the admin audit modal on top
const RootNavigator = ({ handleLogout }: { handleLogout: () => void }) => (
  <RootStack.Navigator
    screenOptions={{ headerShown: false, presentation: 'modal' }}
  >
    <RootStack.Screen name="Main">
      {() => <MainTabs handleLogout={handleLogout} />}
    </RootStack.Screen>

    {/* Admin-only: full-screen modal audit dashboard */}
    <RootStack.Screen
      name="AuditModal"
      component={AuditDashboardScreen}
      options={{
        headerShown: true,
        title: 'Security Audit Logs',
        headerStyle: {
          backgroundColor: COLORS.primaryDark,
          elevation: 0,
          shadowOpacity: 0,
        },
        headerTintColor: COLORS.textOnDark,
        headerTitleStyle: {
          ...TYPOGRAPHY.h4,
          color: COLORS.textOnDark,
        },
        presentation: 'fullScreenModal',
      }}
    />
  </RootStack.Navigator>
);

// ── App Navigator (auth gate) ─────────────────────────────────────────────────
const AppNavigator = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLogin = useCallback((success: boolean) => {
    if (success) setIsLoggedIn(true);
  }, []);

  const handleLogout = useCallback(() => {
    setIsLoggedIn(false);
  }, []);

  return (
    <NavigationContainer>
      {!isLoggedIn ? (
        // Auth is rendered directly — no navigator wrapper so no header
        <AuthScreen onLoginSuccess={handleLogin} />
      ) : (
        <RootNavigator handleLogout={handleLogout} />
      )}
    </NavigationContainer>
  );
};

export default AppNavigator;

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  // Header
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: SPACING.lg,
  },
  headerIconBtn: {
    padding: SPACING.xs,
    position: 'relative',
  },
  notifDot: {
    position: 'absolute',
    top: 2,
    right: 2,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: COLORS.accent,
    borderWidth: 1.5,
    borderColor: COLORS.primaryDark,
  },

  // Tab bar
  tabBar: {
    flexDirection: 'row',
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    paddingTop: SPACING.sm,
    ...SHADOWS.small,
  },
  tabItem: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'flex-start',
    paddingTop: 4,
    position: 'relative',
  },
  tabActivePill: {
    position: 'absolute',
    top: -SPACING.sm,
    width: 28,
    height: 3,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.primary,
  },
  tabLabel: {
    ...TYPOGRAPHY.caption,
    marginTop: 3,
    fontWeight: '500',
    letterSpacing: 0.1,
  },

  // Placeholder Profile screen
  placeholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.background,
    gap: SPACING.md,
  },
  placeholderTitle: {
    ...TYPOGRAPHY.h3,
    color: COLORS.text,
    marginTop: SPACING.sm,
  },
  placeholderSub: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
  },
  adminBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    backgroundColor: COLORS.primaryDark,
    paddingHorizontal: SPACING.xl,
    paddingVertical: SPACING.md,
    borderRadius: BORDER_RADIUS.lg,
    marginTop: SPACING.xl,
    ...SHADOWS.medium,
  },
  adminBtnText: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.textOnDark,
  },
});