// src/components/common/GlossaryPopup.tsx
// SecureWealth Twin -- Glossary Popup
//
// Changes from original:
//  - Dictionary restructured to SNAKE_CASE keys with {title, body} shape,
//    matching the local GLOSSARY dicts already in TransactionInitiateScreen,
//    WealthOverviewScreen, and PhishingScannerScreen. Those screens have
//    // TODO Batch 6 markers -- once this file is in the repo, replace their
//    local showGlossary() Alert + local GLOSSARY dict with this component.
//    Keys that map 1:1: IMPS, NEFT, RTGS, UPI, FD, RD, SIP, EMI, NET_WORTH,
//    EMERGENCY_FUND.
//  - Added animated scale+fade on open (consistent with SecurityReviewScreen).
//  - Added "Got it" button so users know how to dismiss without guessing.
//  - Tap outside the card also closes the modal.

import React, { useRef, useState } from 'react';
import {
  TouchableOpacity,
  Text,
  Modal,
  View,
  StyleSheet,
  Animated,
  Easing,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS } from '../../constants/theme';
import Card from './Card';

const GLOSSARY_TERMS = {
  // Banking
  MPIN: {
    title: 'MPIN',
    body: 'A 4 to 6 digit PIN you set up for mobile banking. You enter this to log in and confirm certain actions in the app.',
  },
  SAVINGS_ACCOUNT: {
    title: 'Savings Account',
    body: 'An account designed for saving money. It earns interest on your balance and is meant for occasional withdrawals rather than everyday spending.',
  },
  CURRENT_ACCOUNT: {
    title: 'Current Account',
    body: "An account designed for frequent transactions, often used by businesses. It typically doesn't earn interest but allows unlimited deposits and withdrawals.",
  },
  SALARY_ACCOUNT: {
    title: 'Salary Account',
    body: 'A savings account set up by your employer to receive your monthly salary. It often comes with extra benefits like fee waivers.',
  },
  FD: {
    title: 'FD (Fixed Deposit)',
    body: 'You deposit a lump sum for a fixed period and earn a fixed interest rate. Your money is locked in but earns more than a regular savings account.',
  },
  RD: {
    title: 'RD (Recurring Deposit)',
    body: 'You deposit a fixed amount every month for a set period and earn interest on it -- a good way to build a savings habit.',
  },
  UPI: {
    title: 'UPI (Unified Payments Interface)',
    body: 'Instant transfer using a UPI ID or phone number -- available 24/7, including bank holidays.',
  },
  IMPS: {
    title: 'IMPS (Immediate Payment Service)',
    body: 'Money reaches the recipient within minutes -- any time, day or night, including weekends and holidays.',
  },
  NEFT: {
    title: 'NEFT (National Electronic Funds Transfer)',
    body: 'A standard transfer that usually completes within a few hours on banking days. Good for non-urgent payments.',
  },
  RTGS: {
    title: 'RTGS (Real Time Gross Settlement)',
    body: 'Designed for large amounts (Rs 2 lakh and above). Each payment is settled individually and immediately during banking hours.',
  },
  EMI: {
    title: 'EMI (Equated Monthly Instalment)',
    body: 'The fixed amount you pay every month towards repaying a loan, covering both the loan amount and interest.',
  },
  // Security
  RISK_SCORE: {
    title: 'Risk Score',
    body: 'A number our system calculates for every transaction to estimate how unusual it looks. A higher score means more checks happen before the payment goes through.',
  },
  DEVICE_TRUST: {
    title: 'Device Trust',
    body: "Whether we recognise the phone or computer you are using for banking. New or unrecognised devices get extra checks to keep your account safe.",
  },
  OTP: {
    title: 'OTP (One-Time Password)',
    body: 'A temporary code sent to your phone to confirm it is really you. Never share this with anyone -- not even bank staff.',
  },
  PHISHING: {
    title: 'Phishing',
    body: 'A scam where someone pretends to be a trusted organisation (like your bank) to trick you into sharing sensitive information such as your OTP, PIN, or password.',
  },
  // Wealth
  NET_WORTH: {
    title: 'Net Worth',
    body: 'What you own (your accounts and deposits) minus what you owe (your loans). It gives you a single number for your overall financial health.',
  },
  CASH_FLOW: {
    title: 'Cash Flow',
    body: 'The money coming into your accounts (like salary) compared to money going out (like bills and spending) over a period of time.',
  },
  EMERGENCY_FUND: {
    title: 'Emergency Fund',
    body: 'Money set aside purely for unexpected situations -- like a job loss or medical issue -- usually enough to cover 3 to 6 months of expenses.',
  },
  SIP: {
    title: 'SIP (Systematic Investment Plan)',
    body: 'You invest a fixed amount regularly (usually monthly). Over the long term, this can help your money grow.',
  },
} as const;

export type GlossaryTermKey = keyof typeof GLOSSARY_TERMS;

interface GlossaryPopupProps {
  term: GlossaryTermKey;
  children?: React.ReactNode;
}

const GlossaryPopup: React.FC<GlossaryPopupProps> = ({ term, children }) => {
  const [isVisible, setIsVisible] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.94)).current;

  const entry = GLOSSARY_TERMS[term];
  if (!entry) return children ? <>{children}</> : null;

  const open = () => {
    setIsVisible(true);
    fadeAnim.setValue(0);
    scaleAnim.setValue(0.94);
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 200, useNativeDriver: true }),
      Animated.timing(scaleAnim, {
        toValue: 1,
        duration: 200,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
    ]).start();
  };

  const close = () => setIsVisible(false);

  return (
    <>
      <TouchableOpacity onPress={open} activeOpacity={0.6} hitSlop={8} style={styles.trigger}>
        {children || <Feather name="help-circle" size={16} color={COLORS.textTertiary} />}
      </TouchableOpacity>

      <Modal visible={isVisible} transparent animationType="none" onRequestClose={close}>
        <Animated.View style={[styles.overlay, { opacity: fadeAnim }]}>
          <TouchableOpacity style={StyleSheet.absoluteFill} activeOpacity={1} onPress={close} />
          <Animated.View style={[styles.cardWrap, { transform: [{ scale: scaleAnim }] }]}>
            <TouchableOpacity activeOpacity={1}>
              <Card padding="lg">
                <View style={styles.header}>
                  <View style={styles.headerIconWrap}>
                    <Feather name="info" size={13} color={COLORS.primary} />
                  </View>
                  <Text style={styles.termTitle} numberOfLines={2}>
                    {entry.title}
                  </Text>
                  <TouchableOpacity onPress={close} hitSlop={8}>
                    <Feather name="x" size={20} color={COLORS.textTertiary} />
                  </TouchableOpacity>
                </View>
                <Text style={styles.body}>{entry.body}</Text>
                <TouchableOpacity style={styles.gotItBtn} onPress={close} activeOpacity={0.8}>
                  <Text style={styles.gotItText}>Got it</Text>
                </TouchableOpacity>
              </Card>
            </TouchableOpacity>
          </Animated.View>
        </Animated.View>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  trigger: {
    padding: 2,
  },
  overlay: {
    flex: 1,
    backgroundColor: COLORS.overlay,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: SPACING.xl,
  },
  cardWrap: {
    width: '100%',
    maxWidth: 400,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: SPACING.sm,
    marginBottom: SPACING.md,
  },
  headerIconWrap: {
    width: 24,
    height: 24,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.primaryVeryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 2,
    flexShrink: 0,
  },
  termTitle: {
    ...TYPOGRAPHY.h4,
    fontWeight: '700',
    color: COLORS.text,
    flex: 1,
  },
  body: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    lineHeight: 21,
    marginBottom: SPACING.lg,
  },
  gotItBtn: {
    alignSelf: 'flex-end',
    backgroundColor: COLORS.primaryVeryLight,
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.sm,
    borderRadius: BORDER_RADIUS.md,
  },
  gotItText: {
    ...TYPOGRAPHY.bodySmMedium,
    color: COLORS.primary,
    fontWeight: '700',
  },
});

export default GlossaryPopup;