// src/navigation/index.tsx
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createDrawerNavigator } from '@react-navigation/drawer';
import { createStackNavigator } from '@react-navigation/stack';
import { TouchableOpacity, View, Text } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { BORDER_RADIUS, SPACING, TYPOGRAPHY } from '../constants/theme';

// Import screens (we'll create these later)
import AuthScreen from '../screens/AuthScreen';
import DashboardScreen from '../screens/DashboardScreen';
import TransactionInitiateScreen from '../screens/TransactionInitiateScreen';
import SecurityReviewScreen from '../screens/SecurityReviewScreen';
import TransactionResultScreen from '../screens/TransactionResultScreen';
import WealthOverviewScreen from '../screens/WealthOverviewScreen';
import PhishingScannerScreen from '../screens/PhishingScannerScreen';
import AuditDashboardScreen from '../screens/AuditDashboardScreen';

const Drawer = createDrawerNavigator();
const Stack = createStackNavigator();

// Main App Stack Navigator
const AppStack = () => {
  return (
    <Stack.Navigator
      initialRouteName="Dashboard"
      screenOptions={{
        headerStyle: {
          backgroundColor: COLORS.primaryDark,
        },
        headerTintColor: COLORS.textOnDark,
        headerTitleStyle: {
          ...TYPOGRAPHY.h4,
          fontWeight: '600',
        },
      }}
    >
      <Stack.Screen 
        name="Dashboard" 
        component={DashboardScreen}
        options={({ navigation }) => ({
          title: 'SecureWealth Twin',
          headerLeft: () => (
            <TouchableOpacity 
              onPress={() => navigation.openDrawer()}
              style={{ marginLeft: SPACING.lg }}
            >
              <Feather name="menu" size={24} color={COLORS.textOnDark} />
            </TouchableOpacity>
          ),
        })}
      />
      <Stack.Screen 
        name="TransactionInitiate" 
        component={TransactionInitiateScreen}
        options={{ title: 'Transfer Money' }}
      />
      <Stack.Screen 
        name="SecurityReview" 
        component={SecurityReviewScreen}
        options={{ title: 'Security Review' }}
      />
      <Stack.Screen 
        name="TransactionResult" 
        component={TransactionResultScreen}
        options={{ title: 'Transaction Result' }}
      />
      <Stack.Screen 
        name="WealthOverview" 
        component={WealthOverviewScreen}
        options={{ title: 'Wealth Overview' }}
      />
      <Stack.Screen 
        name="PhishingScanner" 
        component={PhishingScannerScreen}
        options={{ title: 'Phishing Scanner' }}
      />
      <Stack.Screen 
        name="AuditDashboard" 
        component={AuditDashboardScreen}
        options={{ title: 'Audit Dashboard' }}
      />
    </Stack.Navigator>
  );
};

// Drawer Content Component
const CustomDrawerContent = (props: any) => {
  const menuItems = [
    { label: 'Dashboard', icon: 'home', screen: 'Dashboard' },
    { label: 'Wealth', icon: 'pie-chart', screen: 'WealthOverview' },
    { label: 'Security', icon: 'shield', screen: 'SecurityReview' },
    { label: 'Phishing Scanner', icon: 'alert-triangle', screen: 'PhishingScanner' },
    { label: 'Audit Logs', icon: 'clipboard', screen: 'AuditDashboard' },
    { label: 'Settings', icon: 'settings', screen: 'Settings' },
    { label: 'Logout', icon: 'power', screen: 'Logout' },
  ];

  return (
    <View style={{ flex: 1, backgroundColor: COLORS.surface }}>
      <View style={{ 
        height: 120, 
        backgroundColor: COLORS.primaryDark, 
        justifyContent: 'center', 
        alignItems: 'center',
        padding: SPACING.lg,
      }}>
        <Feather name="shield" size={32} color={COLORS.textOnDark} />
        <Text style={{ 
          ...TYPOGRAPHY.h4, 
          color: COLORS.textOnDark, 
          fontWeight: '600',
          marginTop: SPACING.sm,
        }}>
          SecureWealth Twin
        </Text>
      </View>
      
      <View style={{ flex: 1, padding: SPACING.lg }}>
        {menuItems.map((item, index) => (
          <TouchableOpacity
            key={index}
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              paddingVertical: SPACING.md,
              paddingHorizontal: SPACING.sm,
              borderRadius: BORDER_RADIUS.md,
              marginVertical: SPACING.xs,
              ...(item.screen === 'Logout' ? { marginTop: SPACING.xxl } : {}),
            }}
            onPress={() => {
              if (item.screen === 'Logout') {
                console.log('Logout pressed');
              } else {
                props.navigation.navigate('AppStack', {
                  screen: item.screen,
                });
                props.navigation.closeDrawer();
              }
            }}
          >
            <Feather name={item.icon as any} size={20} color={COLORS.primary} />
            <Text style={{ 
              ...TYPOGRAPHY.body, 
              color: COLORS.text, 
              marginLeft: SPACING.md,
              fontWeight: item.screen === 'Dashboard' ? '600' : '400',
            }}>
              {item.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
};

// Main Navigation Component
const AppNavigator = () => {
  return (
    <NavigationContainer>
      <Drawer.Navigator
        initialRouteName="AppStack"
        drawerContent={CustomDrawerContent}
        screenOptions={{
          drawerActiveBackgroundColor: COLORS.primaryLight,
          drawerActiveTintColor: COLORS.primary,
          drawerInactiveTintColor: COLORS.textSecondary,
          drawerLabelStyle: {
            ...TYPOGRAPHY.body,
            marginLeft: -20,
          },
        }}
      >
        <Drawer.Screen name="AppStack" component={AppStack} options={{ headerShown: false }} />
      </Drawer.Navigator>
    </NavigationContainer>
  );
};

export default AppNavigator;