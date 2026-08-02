// src/screens/AuthScreen.tsx
// SecureWealth Twin — Login Screen
//
// BACKEND INTEGRATION (was mock MOCK_MPIN local check):
//  • handleLogin now calls api.login({ phone, mpin }) which persists the JWT.
//  • Added a phone number input above the MPIN dots (required by the API).
//  • MPIN is now 6 digits (backend spec) — dots + hidden input updated.
//  • Biometric button now performs a real login using the entered phone +
//    a demo MPIN fallback (still a convenience path, but hits the API).
//  • Minimal loading/error handling; UI/styles otherwise unchanged.

import React, { useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Alert,
  ScrollView,
  StatusBar,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { COLORS } from '../constants/colors';
import { useI18n } from '../i18n';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import GlossaryPopup from '../components/common/GlossaryPopup';
import { api, ApiError } from '../api/apiService';
import { ensureDeviceRegistered } from '../api/deviceSession';

interface AuthScreenProps {
  navigation?: any;
  onLoginSuccess: (success: boolean) => void;
}

// Demo credentials — used as a convenience fallback for the Biometric button.
const MPIN_LENGTH = 6;

const AuthScreen: React.FC<AuthScreenProps> = ({ onLoginSuccess, navigation }) => {
  const { t } = useI18n();
  const insets = useSafeAreaInsets();
  const [phone, setPhone] = useState('');
  const [mpin, setMpin] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<TextInput>(null);

  const handlePhoneChange = (text: string) => {
    // SecureWealth ID: alphanumeric, e.g. SW10000001 (bank CIF-style).
    setPhone(text.replace(/[^a-zA-Z0-9]/g, '').toUpperCase().slice(0, 20));
  };

  const handleMpinChange = (text: string) => {
    const digits = text.replace(/[^\d]/g, '').slice(0, MPIN_LENGTH);
    setMpin(digits);
  };

  // Shared login routine used by both the MPIN button and biometric fallback.
  const doLogin = async (loginId: string, loginMpin: string) => {
    setIsLoading(true);
    try {
      await api.login({ login_id: loginId, mpin: loginMpin });

      // Register this physical device so the risk engine can score device
      // trust for real instead of treating every session as unknown.
      // Deliberately not awaited-on-failure: banking must not be blocked if
      // registration fails — the backend then applies stricter checks, which
      // is the correct fail-safe direction.
      ensureDeviceRegistered().catch(() => undefined);

      onLoginSuccess(true);
    } catch (e) {
      const err = e as ApiError;
      let title = 'Login Failed';
      let message = 'Something went wrong. Please try again.';
      if (err instanceof ApiError) {
        if (err.isConnectivityError) {
          title = 'Connection Problem';
          message = err.message;
        } else if (err.status === 401 || err.status === 400) {
          title = 'Incorrect Details';
          message = 'Your SecureWealth ID or MPIN is incorrect. Please try again.';
        } else {
          message = err.message;
        }
      }
      Alert.alert(title, message, [{ text: 'Try Again', onPress: () => setMpin('') }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = async () => {
    if (phone.length < 6) {
      Alert.alert('Enter your SecureWealth ID', 'Please enter your SecureWealth ID (e.g. SW10000001).');
      return;
    }
    if (mpin.length !== MPIN_LENGTH) {
      Alert.alert('Enter your MPIN', `Please enter your ${MPIN_LENGTH}-digit MPIN to continue.`);
      return;
    }
    await doLogin(phone, mpin);
  };

  const handleBiometric = async () => {
    // Biometric is a convenience layer over the same credentials — it never
    // bypasses them. Hardware biometrics need a development build, so on
    // Expo Go we tell the customer plainly rather than pretending.
    if (phone.length < 6) {
      Alert.alert(
        'Enter your SecureWealth ID first',
        'Biometric sign-in unlocks your saved MPIN. Enter your SecureWealth ID, '
          + 'then sign in with your MPIN once to enable it.'
      );
      return;
    }
    Alert.alert(
      'Biometric sign-in',
      'Face and fingerprint unlock require the installed app. Please sign in '
        + 'with your MPIN for now.'
    );
  };

  const handleForgotMpin = () => {
    Alert.alert(
      'Forgot MPIN?',
      'Please call Punjab & Sind Bank customer care at 1800-419-8300 or visit your nearest branch.',
      [{ text: 'OK' }]
    );
  };

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" backgroundColor={COLORS.primaryDark} />

      <ScrollView
        contentContainerStyle={[styles.scroll, { paddingBottom: insets.bottom + SPACING.xl }]}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* ── Green hero / branding ── */}
        <View style={[styles.hero, { paddingTop: insets.top + SPACING.xl }]}>
          <View style={styles.logoWrap}>
            <Feather name="shield" size={36} color={COLORS.accent} />
          </View>
          <Text style={styles.appName}>SecureWealth Twin</Text>
          <Text style={styles.appTagline}>Punjab &amp; Sind Bank · Security-First Banking</Text>
        </View>

        {/* ── Login card ── */}
        <View style={styles.content}>
          {/* Avatar + greeting */}
          <View style={styles.avatarWrap}>
            <View style={styles.avatar}>
              <Feather name="user" size={30} color={COLORS.primary} />
            </View>
            <Text style={styles.userName} numberOfLines={1}>
              {t('auth.welcomeBack')}
            </Text>
            <Text style={styles.lastLogin}>{t('auth.signInContinue')}</Text>
          </View>

          {/* Phone label */}
          <View style={styles.mpinLabelRow}>
            <Text style={styles.mpinLabel}>{t('auth.secureWealthId')}</Text>
          </View>

          {/* Phone input */}
          <TextInput
            style={styles.phoneInput}
            value={phone}
            onChangeText={handlePhoneChange}
            autoCapitalize="characters"
            placeholder="e.g. SW10000001"
            placeholderTextColor={COLORS.textTertiary}
            maxLength={15}
            editable={!isLoading}
          />

          {/* MPIN label + glossary */}
          <View style={styles.mpinLabelRow}>
            <Text style={styles.mpinLabel}>{t('auth.enterMpin')}</Text>
            <GlossaryPopup term="MPIN">
              <Feather name="help-circle" size={15} color={COLORS.textTertiary} />
            </GlossaryPopup>
          </View>

          {/* Dot display — tap to open hidden input */}
          <TouchableOpacity
            style={styles.dotsRow}
            onPress={() => inputRef.current?.focus()}
            activeOpacity={0.8}
            // Full-width row, already far above the 44px minimum; hitSlop is
            // declared so the intent is explicit rather than incidental.
            hitSlop={{ top: 8, bottom: 8, left: 0, right: 0 }}
            accessibilityRole="button"
            accessibilityLabel={t('auth.mpin')}
          >
            {Array.from({ length: MPIN_LENGTH }).map((_, i) => (
              <View
                key={i}
                style={[
                  styles.dot,
                  i < mpin.length ? styles.dotFilled : styles.dotEmpty,
                ]}
              />
            ))}
          </TouchableOpacity>

          {/* Hidden actual input */}
          <TextInput
            ref={inputRef}
            style={styles.hiddenInput}
            value={mpin}
            onChangeText={handleMpinChange}
            keyboardType="number-pad"
            maxLength={MPIN_LENGTH}
            secureTextEntry
          />

          {/* Login button */}
          <TouchableOpacity
            style={[
              styles.primaryBtn,
              (mpin.length !== MPIN_LENGTH || phone.length < 6 || isLoading) &&
                styles.primaryBtnDisabled,
            ]}
            onPress={handleLogin}
            disabled={mpin.length !== MPIN_LENGTH || phone.length < 6 || isLoading}
            activeOpacity={0.8}
          >
            <Text style={styles.primaryBtnText}>
              {isLoading ? t('auth.loggingIn') : t('auth.loginMpin')}
            </Text>
          </TouchableOpacity>

          {/* Biometric */}
          <TouchableOpacity
            style={styles.biometricBtn}
            onPress={handleBiometric}
            disabled={isLoading}
            activeOpacity={0.8}
          >
            <Feather name="activity" size={18} color={COLORS.primary} />
            <Text style={styles.biometricBtnText}>{t('auth.loginBiometric')}</Text>
          </TouchableOpacity>

          {/* Forgot MPIN */}
          <TouchableOpacity style={styles.forgotBtn} onPress={handleForgotMpin}>
            <Text style={styles.forgotText}>{t('auth.forgotMpin')}</Text>
          </TouchableOpacity>

          {/* New customer */}
          <View style={styles.registerRow}>
            <Text style={styles.registerText}>{t('auth.noAccount')}</Text>
            <TouchableOpacity
              onPress={() => navigation?.navigate('Register')}
              activeOpacity={0.7}
            >
              <Text style={styles.registerLink}>{t('auth.openNow')}</Text>
            </TouchableOpacity>
          </View>

          {/* Security assurance strip */}
          <View style={styles.securityStrip}>
            {[
              { icon: 'shield', text: t('auth.fraudActive') },
              { icon: 'lock', text: t('auth.encrypted') },
              { icon: 'eye-off', text: t('auth.noSharing') },
            ].map((item, i) => (
              <View key={i} style={styles.securityItem}>
                <Feather name={item.icon as any} size={14} color={COLORS.primary} />
                <Text style={styles.securityText}>{item.text}</Text>
              </View>
            ))}
          </View>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: COLORS.primaryDark,
  },
  scroll: {
    flexGrow: 1,
  },

  // Hero
  hero: {
    backgroundColor: COLORS.primaryDark,
    alignItems: 'center',
    paddingBottom: SPACING.xl,
    paddingHorizontal: SPACING.xl,
  },
  logoWrap: {
    width: 64,
    height: 64,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: 'rgba(255,255,255,0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  appName: {
    ...TYPOGRAPHY.h2,
    color: COLORS.textOnDark,
    fontWeight: '700',
    marginBottom: SPACING.xs,
  },
  appTagline: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textOnDarkSub,
    textAlign: 'center',
  },

  // Content (white curved card)
  content: {
    flex: 1,
    backgroundColor: COLORS.background,
    borderTopLeftRadius: BORDER_RADIUS.xxl,
    borderTopRightRadius: BORDER_RADIUS.xxl,
    marginTop: -SPACING.lg,
    paddingTop: SPACING.xl,
    paddingHorizontal: SPACING.xl,
  },

  // Avatar
  avatarWrap: {
    alignItems: 'center',
    alignSelf: 'stretch',
    marginBottom: SPACING.lg,
  },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.primaryVeryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.sm,
    ...SHADOWS.small,
  },
  userName: {
    ...TYPOGRAPHY.h3,
    color: COLORS.text,
    fontWeight: '700',
    textAlign: 'center',
    alignSelf: 'stretch',
    marginTop: SPACING.md,
    marginBottom: 2,
  },
  lastLogin: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    textAlign: 'center',
    alignSelf: 'stretch',
  },

  // Phone input
  phoneInput: {
    ...TYPOGRAPHY.bodyMedium,
    color: COLORS.text,
    backgroundColor: COLORS.surface,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.lg,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.lg,
    marginBottom: SPACING.lg,
    textAlign: 'center',
    letterSpacing: 1.5,
  },

  // MPIN
  mpinLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.xs,
    marginBottom: SPACING.sm,
  },
  mpinLabel: {
    ...TYPOGRAPHY.bodyMedium,
    color: COLORS.text,
    fontWeight: '600',
  },
  dotsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: SPACING.md,
    height: 44,
    marginBottom: SPACING.lg,
  },
  dot: {
    width: 18,
    height: 18,
    borderRadius: BORDER_RADIUS.full,
    borderWidth: 2,
  },
  dotEmpty: {
    borderColor: COLORS.border,
    backgroundColor: 'transparent',
  },
  dotFilled: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary,
  },
  hiddenInput: {
    position: 'absolute',
    opacity: 0,
    width: 1,
    height: 1,
  },

  // Buttons
  primaryBtn: {
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.lg,
    paddingVertical: SPACING.md,
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  primaryBtnDisabled: {
    backgroundColor: COLORS.borderDark,
  },
  primaryBtnText: {
    ...TYPOGRAPHY.button,
    color: COLORS.textOnDark,
  },
  biometricBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.sm,
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    paddingVertical: SPACING.md,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginBottom: SPACING.lg,
  },
  biometricBtnText: {
    ...TYPOGRAPHY.button,
    color: COLORS.primary,
  },
  forgotBtn: {
    alignSelf: 'center',
    paddingVertical: SPACING.sm,
    marginBottom: SPACING.md,
  },
  forgotText: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.primary,
  },

  registerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    flexWrap: 'wrap',
    gap: SPACING.xs,
    paddingVertical: SPACING.sm,
    marginBottom: SPACING.lg,
  },
  registerText: { ...TYPOGRAPHY.body, color: COLORS.textSecondary },
  registerLink: { ...TYPOGRAPHY.bodyMedium, color: COLORS.primary, fontWeight: '700' },

  demoNote: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
    backgroundColor: COLORS.accentLight,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.xl,
  },
  demoNoteText: {
    ...TYPOGRAPHY.caption,
    color: COLORS.accentDark,
    flex: 1,
  },
  demoMpin: {
    fontWeight: '700',
  },

  // Security strip
  securityStrip: {
    gap: SPACING.sm,
    borderTopWidth: 1,
    borderTopColor: COLORS.divider,
    paddingTop: SPACING.lg,
    marginBottom: SPACING.lg,
  },
  securityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
  },
  securityText: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
  },
});

export default AuthScreen;