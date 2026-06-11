// src/screens/AuthScreen.tsx
import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, TextInput, Alert } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import Card from '../components/common/Card';
import RiskBadge from '../components/common/RiskBadge';

const AuthScreen = () => {
  const [mpin, setMpin] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async () => {
    if (mpin.length !== 6) {
      Alert.alert('Invalid MPIN', 'MPIN must be 6 digits');
      return;
    }

    setIsLoading(true);
    try {
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      console.log('Login successful with MPIN:', mpin);
      // Navigate to dashboard
    } catch (error) {
      console.error('Login failed:', error);
      Alert.alert('Login Failed', 'Please try again');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBiometricLogin = async () => {
    setIsLoading(true);
    try {
      // Mock biometric authentication
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log('Biometric login successful');
      // Navigate to dashboard
    } catch (error) {
      console.error('Biometric failed:', error);
      Alert.alert('Biometric Failed', 'Please use MPIN instead');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* Header with PSB branding */}
      <View style={styles.header}>
        <Feather name="shield" size={48} color={COLORS.primary} />
        <Text style={styles.title}>SecureWealth Twin</Text>
        <Text style={styles.subtitle}>Security-First Banking Platform</Text>
      </View>

      <Card style={styles.loginCard}>
        {/* User Avatar */}
        <View style={styles.avatarContainer}>
          <View style={styles.avatar}>
            <Feather name="user" size={32} color={COLORS.primary} />
          </View>
          <Text style={styles.userName}>Swayam Kohli</Text>
          <RiskBadge level="LOW" showIcon={true} size="sm" />
        </View>

        {/* MPIN Input */}
        <View style={styles.mpinContainer}>
          <Text style={styles.mpinLabel}>Enter your 6-digit MPIN</Text>
          <View style={styles.mpinInputContainer}>
            {Array.from({ length: 6 }).map((_, index) => (
              <View key={index} style={styles.mpinDigitContainer}>
                <TextInput
                  style={styles.mpinDigit}
                  value={mpin[index] || ''}
                  maxLength={1}
                  keyboardType="number-pad"
                  secureTextEntry
                  autoFocus={index === 0}
                  caretHidden
                  onChangeText={(text) => {
                    if (text && mpin.length === index) {
                      setMpin(mpin + text);
                      if (index < 5) {
                        // Focus next input (would need refs in real implementation)
                      }
                    }
                  }}
                  onKeyPress={(e) => {
                    if (e.nativeEvent.key === 'Backspace' && mpin.length > index) {
                      setMpin(mpin.slice(0, -1));
                    }
                  }}
                />
              </View>
            ))}
          </View>
        </View>

        {/* Login Buttons */}
        <View style={styles.buttonContainer}>
          <TouchableOpacity 
            style={[styles.loginButton, styles.mpinButton]}
            onPress={handleLogin}
            disabled={isLoading || mpin.length !== 6}
          >
            <Text style={styles.buttonText}>
              {isLoading ? 'Processing...' : 'Login with MPIN'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.loginButton, styles.biometricButton]}
            onPress={handleBiometricLogin}
            disabled={isLoading}
          >
            <Feather name="fingerprint" size={20} color={COLORS.textOnDark} />
            <Text style={[styles.buttonText, styles.biometricText]}>Login with Biometric</Text>
          </TouchableOpacity>
        </View>

        {/* Forgot MPIN */}
        <TouchableOpacity style={styles.forgotButton}>
          <Text style={styles.forgotText}>Forgot MPIN?</Text>
        </TouchableOpacity>
      </Card>

      {/* Security Features */}
      <View style={styles.featuresContainer}>
        <Text style={styles.featuresTitle}>Security Features</Text>
        <View style={styles.featureList}>
          <View style={styles.featureItem}>
            <Feather name="shield" size={20} color={COLORS.primary} />
            <Text style={styles.featureText}>Biometric Authentication</Text>
          </View>
          <View style={styles.featureItem}>
            <Feather name="lock" size={20} color={COLORS.primary} />
            <Text style={styles.featureText}>End-to-End Encryption</Text>
          </View>
          <View style={styles.featureItem}>
            <Feather name="eye-off" size={20} color={COLORS.primary} />
            <Text style={styles.featureText}>Zero-Knowledge Architecture</Text>
          </View>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    padding: SPACING.lg,
  },
  header: {
    alignItems: 'center',
    marginBottom: SPACING.xxl,
    marginTop: SPACING.xxl,
  },
  title: {
    ...TYPOGRAPHY.h2,
    fontWeight: '700',
    color: COLORS.primary,
    marginTop: SPACING.sm,
  },
  subtitle: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginTop: SPACING.xs,
  },
  loginCard: {
    padding: SPACING.xl,
    marginBottom: SPACING.lg,
  },
  avatarContainer: {
    alignItems: 'center',
    marginBottom: SPACING.xxl,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: COLORS.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  userName: {
    ...TYPOGRAPHY.h4,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.xs,
  },
  mpinContainer: {
    marginBottom: SPACING.xxl,
  },
  mpinLabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginBottom: SPACING.md,
    textAlign: 'center',
  },
  mpinInputContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: SPACING.md,
  },
  mpinDigitContainer: {
    width: 50,
    height: 60,
  },
  mpinDigit: {
    flex: 1,
    borderWidth: 2,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.md,
    textAlign: 'center',
    fontSize: 24,
    fontWeight: '600',
    color: COLORS.text,
  },
  buttonContainer: {
    marginBottom: SPACING.md,
  },
  loginButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: SPACING.lg,
    borderRadius: BORDER_RADIUS.lg,
    marginBottom: SPACING.sm,
  },
  mpinButton: {
    backgroundColor: COLORS.primary,
  },
  biometricButton: {
    backgroundColor: COLORS.primaryDark,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: {
    ...TYPOGRAPHY.button,
    color: COLORS.textOnDark,
  },
  biometricText: {
    marginLeft: SPACING.sm,
  },
  forgotButton: {
    alignSelf: 'center',
  },
  forgotText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.primary,
    fontWeight: '600',
  },
  featuresContainer: {
    marginTop: SPACING.xxl,
  },
  featuresTitle: {
    ...TYPOGRAPHY.h4,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
    textAlign: 'center',
  },
  featureList: {
    gap: SPACING.sm,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    ...SHADOWS.small,
  },
  featureText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.text,
    marginLeft: SPACING.sm,
    flex: 1,
  },
});

export default AuthScreen;