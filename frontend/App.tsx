// App.tsx
// SecureWealth Twin — Root Entry Point

import React from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import AppNavigator from './src/navigation';
import { I18nProvider } from './src/i18n';

export default function App() {
  return (
    <SafeAreaProvider>
      <I18nProvider>
      {/*
        StatusBar is set to 'auto' so individual screens can control it.
        - Green header screens (Dashboard): light icons on dark bg
        - White content screens: dark icons on light bg
        The navigator handles this via screenOptions per-stack.
      */}
      <StatusBar style="auto" />
        <AppNavigator />
      </I18nProvider>
    </SafeAreaProvider>
  );
}