// src/screens/AuthScreen.tsx
// SecureWealth Twin — Login Screen
//
// Fixes from original:
//  1. RiskBadge removed from login screen — user hasn't authenticated yet,
//     showing a risk level here is meaningless and confusing.
//  2. 6 separate TextInput boxes replaced with a single hidden TextInput +
//     6 display dots. Per-digit inputs don't auto-advance reliably on mobile.
//  3. mpinHelp had flexDirection:'row' on a Text component — invalid, moved
//     to a wrapping View.
//  4. Demo hint card kept but styled clearly as a dev/demo note, not a real
//     banking instruction.
//  5. Layout redesigned: green hero at top (branding), white card below
//     (login form) — matches the PSB UniC reference images from the plan.

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
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import GlossaryPopup from '../components/common/GlossaryPopup';

interface AuthScreenProps {
  onLoginSuccess: (success: boolean) => void;
}

// Demo credentials — displayed clearly as dev note
const MOCK_MPIN = '1234';

const AuthScreen: React.FC<AuthScreenProps> = ({ onLoginSuccess }) => {
  const insets = useSafeAreaInsets();
  const [mpin, setMpin] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<TextInput>(null);

  const handleMpinChange = (text: string) => {
    const digits = text.replace(/[^\d]/g, '').slice(0, 4);
    setMpin(digits);
  };

  const handleLogin = async () => {
    if (mpin.length !== 4) {
      Alert.alert('Enter your MPIN', 'Please enter your 4-digit MPIN to continue.');
      return;
    }
    if (mpin !== MOCK_MPIN) {
      Alert.alert(
        'Incorrect MPIN',
        'That MPIN does not match. Please try again.\n\nDemo hint: use 1234',
        [{ text: 'Try Again', onPress: () => setMpin('') }]
      );
      return;
    }
    setIsLoading(true);
    await new Promise((r) => setTimeout(r, 900));
    setIsLoading(false);
    onLoginSuccess(true);
  };

  const handleBiometric = async () => {
    setIsLoading(true);
    await new Promise((r) => setTimeout(r, 700));
    setIsLoading(false);
    onLoginSuccess(true);
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
              <Feather name="user" size={32} color={COLORS.primary} />
            </View>
            <Text style={styles.userName}>Swayam Kohli</Text>
            <Text style={styles.lastLogin}>Last login: Today, 09:15 AM</Text>
          </View>

          {/* MPIN label + glossary */}
          <View style={styles.mpinLabelRow}>
            <Text style={styles.mpinLabel}>Enter your MPIN</Text>
            <GlossaryPopup term="MPIN">
              <Feather name="help-circle" size={15} color={COLORS.textTertiary} />
            </GlossaryPopup>
          </View>

          {/* Dot display — tap to open hidden input */}
          <TouchableOpacity
            style={styles.dotsRow}
            onPress={() => inputRef.current?.focus()}
            activeOpacity={0.8}
          >
            {Array.from({ length: 4 }).map((_, i) => (
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
            maxLength={4}
            secureTextEntry
            autoFocus
          />

          {/* Login button */}
          <TouchableOpacity
            style={[
              styles.primaryBtn,
              (mpin.length !== 4 || isLoading) && styles.primaryBtnDisabled,
            ]}
            onPress={handleLogin}
            disabled={mpin.length !== 4 || isLoading}
            activeOpacity={0.8}
          >
            <Text style={styles.primaryBtnText}>
              {isLoading ? 'Logging in\u2026' : 'Login with MPIN'}
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
            <Text style={styles.biometricBtnText}>Login with Biometric</Text>
          </TouchableOpacity>

          {/* Forgot MPIN */}
          <TouchableOpacity style={styles.forgotBtn} onPress={handleForgotMpin}>
            <Text style={styles.forgotText}>Forgot MPIN?</Text>
          </TouchableOpacity>

          {/* Demo note */}
          <View style={styles.demoNote}>
            <Feather name="info" size={13} color={COLORS.accentDark} />
            <Text style={styles.demoNoteText}>
              Demo mode — use MPIN <Text style={styles.demoMpin}>1234</Text> or tap Biometric
            </Text>
          </View>

          {/* Security assurance strip */}
          <View style={styles.securityStrip}>
            {[
              { icon: 'shield', text: 'Fraud detection active' },
              { icon: 'lock', text: 'End-to-end encrypted' },
              { icon: 'eye-off', text: 'Zero data sharing' },
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
    paddingBottom: SPACING.xxl,
    paddingHorizontal: SPACING.xl,
  },
  logoWrap: {
    width: 72,
    height: 72,
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
    borderTopLeftRadius: BORDER_RADIUS.xxxl,
    borderTopRightRadius: BORDER_RADIUS.xxxl,
    marginTop: -BORDER_RADIUS.xl,
    paddingTop: SPACING.xl,
    paddingHorizontal: SPACING.xl,
  },

  // Avatar
  avatarWrap: {
    alignItems: 'center',
    marginBottom: SPACING.xl,
  },
  avatar: {
    width: 72,
    height: 72,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.primaryVeryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.sm,
    ...SHADOWS.small,
  },
  userName: {
    ...TYPOGRAPHY.h4,
    color: COLORS.text,
    fontWeight: '700',
    marginBottom: 2,
  },
  lastLogin: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
  },

  // MPIN
  mpinLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.xs,
    marginBottom: SPACING.lg,
  },
  mpinLabel: {
    ...TYPOGRAPHY.bodyMedium,
    color: COLORS.text,
    fontWeight: '600',
  },
  dotsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: SPACING.lg,
    marginBottom: SPACING.xl,
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
    marginBottom: SPACING.xl,
  },
  forgotText: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.primary,
  },

  // Demo note
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