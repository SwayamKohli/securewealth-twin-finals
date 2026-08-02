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
//       │   ├── Tab: Wealth  (LANDING TAB — wealth-first)
//       │   │   └── WealthStack
//       │   │       ├── WealthOverviewScreen
//       │   │       ├── TransactionInitiateScreen (Invest)
//       │   │       ├── SecurityReviewScreen
//       │   │       └── TransactionResultScreen
//       │   ├── Tab: Safety
//       │   │   └── SafetyStack
//       │   │       ├── SafetyHubScreen
//       │   │       ├── PhishingScannerScreen
//       │   │       └── MySecurityActivityScreen
//       │   └── Tab: Profile
//       │       └── ProfileStack
//       │           └── ProfileScreen (placeholder)
//   (Admin audit dashboard REMOVED from mobile — it is a standalone web app.)

import React, { useState, useCallback } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Feather } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { COLORS } from '../constants/colors';
import { useI18n, LANGUAGES } from '../i18n';
import { TYPOGRAPHY, SPACING, BORDER_RADIUS, SHADOWS, TAB_BAR, ANIMATION } from '../constants/theme';

// ── Screens ──────────────────────────────────────────────────────────────────
import AuthScreen from '../screens/AuthScreen';
import RegisterScreen from '../screens/RegisterScreen';
import DashboardScreen from '../screens/DashboardScreen';
import TransactionInitiateScreen from '../screens/TransactionInitiateScreen';
import SecurityReviewScreen from '../screens/SecurityReviewScreen';
import TransactionResultScreen from '../screens/TransactionResultScreen';
import WealthOverviewScreen from '../screens/WealthOverviewScreen';
import SafetyHubScreen from '../screens/SafetyHubScreen';
import PhishingScannerScreen from '../screens/PhishingScannerScreen';
import MySecurityActivityScreen from '../screens/MySecurityActivityScreen';
import ChallengeScreen from '../screens/ChallengeScreen';
import ProfileScreen from '../screens/ProfileScreen';
import ErrorBoundary from '../components/ErrorBoundary';
// REMOVED (admin dashboard is now a STANDALONE WEB APP — /admin-dashboard).
// Kept commented for reference; the mobile app must not expose admin tooling.
// import AuditDashboardScreen from '../screens/AuditDashboardScreen';

// ── Navigator instances ──────────────────────────────────────────────────────
const RootStack = createStackNavigator();
const Tab = createBottomTabNavigator();
const HomeStack = createStackNavigator();
const WealthStack = createStackNavigator();
const SafetyStack = createStackNavigator();
const PhishingStack = createStackNavigator();
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
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
              accessibilityRole="button"
              accessibilityLabel="Notifications"
            >
              <Feather name="bell" size={22} color={COLORS.textOnDark} />
              {/* Notification dot */}
              <View style={styles.notifDot} />
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.headerIconBtn, { marginLeft: SPACING.sm }]}
              onPress={handleLogout}
              activeOpacity={0.7}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
              accessibilityRole="button"
              accessibilityLabel="Sign out"
            >
              <Feather name="log-out" size={20} color={COLORS.textOnDark} />
            </TouchableOpacity>
          </View>
        ),
      })}
    />
  </HomeStack.Navigator>
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
    {/* Task 1.2/2.3 — Invest flow lives INSIDE Wealth (wealth-first UX) */}
    <WealthStack.Screen
      name="TransactionInitiate"
      component={TransactionInitiateScreen}
      options={{ title: 'Invest' }}
    />
    <WealthStack.Screen
      name="SecurityReview"
      component={SecurityReviewScreen}
      options={{
        title: 'Security Check',
        headerLeft: () => null,
        gestureEnabled: false,
      }}
    />
    <WealthStack.Screen
      name="Challenge"
      component={ChallengeScreen}
      options={{
        title: 'Verify Identity',
        headerLeft: () => null,
        gestureEnabled: false,
      }}
    />
    <WealthStack.Screen
      name="TransactionResult"
      component={TransactionResultScreen}
      options={{
        title: 'Investment Status',
        headerLeft: () => null,
        gestureEnabled: false,
      }}
    />
  </WealthStack.Navigator>
);

// ── Phishing Protection Stack (dedicated tab, task 1.1) ──────────────────────
const PhishingStackNavigator = () => (
  <PhishingStack.Navigator screenOptions={sharedStackScreenOptions}>
    <PhishingStack.Screen
      name="PhishingScanner"
      component={PhishingScannerScreen}
      options={{
        title: 'Phishing Protection',
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
  </PhishingStack.Navigator>
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
        title: 'Security',
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
      name="MySecurityActivity"
      component={MySecurityActivityScreen}
      options={{ title: 'My Security Activity' }}
    />
  </SafetyStack.Navigator>
);

// ── Tab 5: Profile Stack ─────────────────────────────────────────────────────
// REPLACED (M1 task 3) — the real ProfileScreen now shows live identity,
// registered devices with trust status, the aggregation consent toggle, the
// language switcher and a proper server-side logout. Kept here, commented out,
// as a record of the mid-evaluation placeholder.
// const PlaceholderProfileScreen = ({ navigation }: any) => {
//   const { t, language, setLanguage } = useI18n();
//   return (
//   <View style={styles.placeholder}>
//     <Feather name="user" size={48} color={COLORS.textTertiary} />
//     <Text style={styles.placeholderTitle}>{t('profile.title')}</Text>
//
//     {/* Task 1.5 — language switcher (EN / HI / PA) */}
//     <Text style={styles.langLabel}>{t('profile.chooseLanguage')}</Text>
//     <View style={styles.langRow}>
//       {LANGUAGES.map((l) => (
//         <TouchableOpacity
//           key={l.code}
//           style={[styles.langBtn, language === l.code && styles.langBtnActive]}
//           onPress={() => setLanguage(l.code)}
//           activeOpacity={0.8}
//         >
//           <Text
//             style={[
//               styles.langBtnText,
//               language === l.code && styles.langBtnTextActive,
//             ]}
//           >
//             {l.native}
//           </Text>
//         </TouchableOpacity>
//       ))}
//     </View>
//     // REMOVED — the Admin Audit Dashboard is a separate WEB application
//     // (/admin-dashboard). Customers must never see admin tooling.
//   </View>
//   );
// };

const ProfileStackNavigator = ({ handleLogout }: { handleLogout: () => void }) => (
  <ProfileStack.Navigator screenOptions={sharedStackScreenOptions}>
    <ProfileStack.Screen name="Profile" options={{ title: 'My Profile' }}>
      {() => <ProfileScreen handleLogout={handleLogout} />}
    </ProfileStack.Screen>
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
  const { t } = useI18n();

  // Task 1.1 — Wealth-first navigation order (labels localised, task 1.5)
  const tabs = [
    { icon: 'home', label: t('tab.home') },
    { icon: 'trending-up', label: t('tab.wealth') },
    { icon: 'shield', label: t('tab.security') },
    { icon: 'message-square', label: t('tab.phishing') },
    { icon: 'user', label: t('tab.profile') },
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
    initialRouteName="WealthTab"
  >
    <Tab.Screen name="HomeTab">
      {() => <HomeStackNavigator handleLogout={handleLogout} />}
    </Tab.Screen>
    <Tab.Screen name="WealthTab" component={WealthStackNavigator} />
    <Tab.Screen name="SafetyTab" component={SafetyStackNavigator} />
    <Tab.Screen name="PhishingTab" component={PhishingStackNavigator} />
    <Tab.Screen name="ProfileTab">
      {() => <ProfileStackNavigator handleLogout={handleLogout} />}
    </Tab.Screen>
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

    {/* REMOVED — audit is a standalone web dashboard now (/admin-dashboard).
    <RootStack.Screen
      name="AuditModal"
      component={AuditDashboardScreen}
      options={{
        headerShown: true,
        title: 'Security Audit Logs',
        headerStyle: { backgroundColor: COLORS.primaryDark },
        headerTintColor: COLORS.textOnDark,
        presentation: 'modal',
      }}
    />
    */}
  </RootStack.Navigator>
);

// ── App Navigator (auth gate) ─────────────────────────────────────────────────
// ── Auth stack: Sign in → Open an account ────────────────────────────────────
const AuthStack = createStackNavigator();

const AuthNavigator = ({ onLoginSuccess }: { onLoginSuccess: (ok: boolean) => void }) => (
  <AuthStack.Navigator screenOptions={{ headerShown: false }}>
    <AuthStack.Screen name="SignIn">
      {(props) => <AuthScreen {...props} onLoginSuccess={onLoginSuccess} />}
    </AuthStack.Screen>
    <AuthStack.Screen
      name="Register"
      component={RegisterScreen}
      options={{ gestureEnabled: true }}
    />
  </AuthStack.Navigator>
);

const AppNavigator = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLogin = useCallback((success: boolean) => {
    if (success) setIsLoggedIn(true);
  }, []);

  const handleLogout = useCallback(() => {
    setIsLoggedIn(false);
  }, []);

  return (
    // Task 21 — a render error anywhere in the tree shows a recoverable screen
    // that states plainly that no money moved, instead of a white screen.
    <ErrorBoundary>
      <NavigationContainer>
        {!isLoggedIn ? (
          <AuthNavigator onLoginSuccess={handleLogin} />
        ) : (
          <RootNavigator handleLogout={handleLogout} />
        )}
      </NavigationContainer>
    </ErrorBoundary>
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
  langLabel: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textSecondary,
    marginTop: SPACING.lg,
    marginBottom: SPACING.sm,
  },
  langRow: {
    flexDirection: 'row',
    gap: SPACING.sm,
    marginBottom: SPACING.md,
  },
  langBtn: {
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.sm,
    borderRadius: 999,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    backgroundColor: COLORS.surface,
  },
  langBtnActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  langBtnText: {
    ...TYPOGRAPHY.body,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  langBtnTextActive: {
    color: COLORS.textOnDark,
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