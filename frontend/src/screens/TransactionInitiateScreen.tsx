// src/screens/TransactionInitiateScreen.tsx
import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, TextInput, ScrollView, Alert } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import Card from '../components/common/Card';
import RiskBadge from '../components/common/RiskBadge';

const TransactionInitiateScreen = () => {
  const [formData, setFormData] = useState({
    fromAccount: '',
    toAccount: '',
    amount: '',
    description: '',
    paymentMode: 'IMPS', // Default
  });
  const [selectedFromAccount, setSelectedFromAccount] = useState<any>(null);
  const [selectedToAccount, setSelectedToAccount] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Mock accounts data
  const accounts = [
    { id: '1', number: '****1234', bank: 'Punjab & Sind Bank', type: 'Savings', balance: 48750 },
    { id: '2', number: '****5678', bank: 'State Bank of India', type: 'Current', balance: 125000 },
  ];

  const paymentModes = [
    { id: 'IMPS', name: 'IMPS', icon: 'zap', description: 'Immediate Payment' },
    { id: 'NEFT', name: 'NEFT', icon: 'clock', description: 'Next Day Settlement' },
    { id: 'RTGS', name: 'RTGS', icon: 'zap', description: 'Large Amounts' },
    { id: 'UPI', name: 'UPI', icon: 'smartphone', description: 'Instant Transfer' },
  ];

  const validateForm = () => {
    if (!selectedFromAccount) {
      Alert.alert('Validation Error', 'Please select a source account');
      return false;
    }
    if (!selectedToAccount) {
      Alert.alert('Validation Error', 'Please enter destination account');
      return false;
    }
    if (!formData.amount || isNaN(Number(formData.amount)) || Number(formData.amount) <= 0) {
      Alert.alert('Validation Error', 'Please enter a valid amount');
      return false;
    }
    if (Number(formData.amount) > selectedFromAccount.balance) {
      Alert.alert('Insufficient Funds', 'Amount exceeds account balance');
      return false;
    }
    return true;
  };

  const handleProceed = async () => {
    if (!validateForm()) return;

    setIsLoading(true);
    try {
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Navigate to security review screen
      console.log('Proceeding to security review...');
    } catch (error) {
      console.error('Transaction failed:', error);
      Alert.alert('Transaction Failed', 'Please try again');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAccountSelect = (account: any, type: 'from' | 'to') => {
    if (type === 'from') {
      setSelectedFromAccount(account);
      setFormData({ ...formData, fromAccount: account.number });
    } else {
      setSelectedToAccount(account);
      setFormData({ ...formData, toAccount: account.number });
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity>
          <Feather name="arrow-left" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Transfer Money</Text>
        <View style={{ width: 24 }} /> {/* Spacer for alignment */}
      </View>

      {/* Risk Level Indicator */}
      <View style={styles.riskHeader}>
        <Text style={styles.riskLabel}>Transaction Risk Level:</Text>
        <RiskBadge level="LOW" showIcon={true} size="md" />
      </View>

      {/* From Account Selection */}
      <Card style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>From Account</Text>
        {selectedFromAccount ? (
          <TouchableOpacity 
            style={styles.selectedAccount}
            onPress={() => setSelectedFromAccount(null)}
          >
            <View style={styles.accountInfo}>
              <Feather name="credit-card" size={24} color={COLORS.primary} />
              <View>
                <Text style={styles.accountNumber}>{selectedFromAccount.number}</Text>
                <Text style={styles.accountBank}>{selectedFromAccount.bank}</Text>
              </View>
            </View>
            <Feather name="chevron-up" size={20} color={COLORS.textSecondary} />
          </TouchableOpacity>
        ) : (
          <View>
            <Text style={styles.placeholderText}>Select source account</Text>
            <View style={styles.accountList}>
              {accounts.map((account) => (
                <TouchableOpacity 
                  key={account.id}
                  style={styles.accountOption}
                  onPress={() => handleAccountSelect(account, 'from')}
                >
                  <View style={styles.accountInfo}>
                    <Feather name="credit-card" size={20} color={COLORS.primary} />
                    <View>
                      <Text style={styles.accountNumber}>{account.number}</Text>
                      <Text style={styles.accountBank}>{account.bank}</Text>
                    </View>
                  </View>
                  <Text style={styles.accountBalance}>₹{account.balance.toLocaleString()}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}
      </Card>

      {/* To Account Input */}
      <Card style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>To Account</Text>
        {selectedToAccount ? (
          <TouchableOpacity 
            style={styles.selectedAccount}
            onPress={() => setSelectedToAccount(null)}
          >
            <View style={styles.accountInfo}>
              <Feather name="user" size={24} color={COLORS.primary} />
              <View>
                <Text style={styles.accountNumber}>{selectedToAccount.number}</Text>
                <Text style={styles.accountBank}>{selectedToAccount.bank}</Text>
              </View>
            </View>
            <Feather name="chevron-up" size={20} color={COLORS.textSecondary} />
          </TouchableOpacity>
        ) : (
          <>
            <TextInput
              style={styles.input}
              placeholder="Enter account number or UPI ID"
              value={formData.toAccount}
              onChangeText={(text) => setFormData({ ...formData, toAccount: text })}
              keyboardType="default"
            />
            <TouchableOpacity style={styles.contactButton}>
              <Feather name="users" size={20} color={COLORS.primary} />
              <Text style={styles.contactButtonText}>Select from contacts</Text>
            </TouchableOpacity>
          </>
        )}
      </Card>

      {/* Amount Input */}
      <Card style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Amount</Text>
        <View style={styles.amountInputContainer}>
          <Text style={styles.currencySymbol}>₹</Text>
          <TextInput
            style={styles.amountInput}
            placeholder="0.00"
            value={formData.amount}
            onChangeText={(text) => setFormData({ ...formData, amount: text.replace(/[^\d.]/g, '') })}
            keyboardType="decimal-pad"
            maxLength={12}
          />
        </View>
      </Card>

      {/* Payment Mode Selection */}
      <Card style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Payment Mode</Text>
        <View style={styles.paymentModeContainer}>
          {paymentModes.map((mode) => (
            <TouchableOpacity
              key={mode.id}
              style={[
                styles.paymentModeOption,
                formData.paymentMode === mode.id && styles.paymentModeSelected
              ]}
              onPress={() => setFormData({ ...formData, paymentMode: mode.id })}
            >
              <Feather name={mode.icon as any} size={24} color={formData.paymentMode === mode.id ? COLORS.primary : COLORS.textSecondary} />
              <Text style={[
                styles.paymentModeText,
                formData.paymentMode === mode.id && styles.paymentModeTextSelected
              ]}>
                {mode.name}
              </Text>
              <Text style={styles.paymentModeDescription}>{mode.description}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </Card>

      {/* Description */}
      <Card style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Description (Optional)</Text>
        <TextInput
          style={[styles.input, styles.descriptionInput]}
          placeholder="Add a note for this transaction"
          value={formData.description}
          onChangeText={(text) => setFormData({ ...formData, description: text })}
          multiline
          numberOfLines={3}
        />
      </Card>

      {/* Proceed Button */}
      <TouchableOpacity 
        style={styles.proceedButton}
        onPress={handleProceed}
        disabled={isLoading}
      >
        <Text style={styles.proceedButtonText}>
          {isLoading ? 'Processing...' : 'Proceed to Security Review'}
        </Text>
        <Feather name="arrow-right" size={20} color={COLORS.textOnDark} />
      </TouchableOpacity>

      {/* Security Features */}
      <View style={styles.securityFeatures}>
        <Text style={styles.securityFeaturesTitle}>Security Features</Text>
        <View style={styles.featureList}>
          <View style={styles.featureItem}>
            <Feather name="shield" size={16} color={COLORS.success} />
            <Text style={styles.featureText}>Real-time fraud detection</Text>
          </View>
          <View style={styles.featureItem}>
            <Feather name="lock" size={16} color={COLORS.success} />
            <Text style={styles.featureText}>End-to-end encryption</Text>
          </View>
          <View style={styles.featureItem}>
            <Feather name="eye" size={16} color={COLORS.success} />
            <Text style={styles.featureText}>Transaction monitoring</Text>
          </View>
        </View>
      </View>
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
  riskHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.lg,
  },
  riskLabel: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginRight: SPACING.sm,
  },
  sectionCard: {
    marginBottom: SPACING.lg,
    padding: SPACING.lg,
  },
  sectionTitle: {
    ...TYPOGRAPHY.h4,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  selectedAccount: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: COLORS.surfaceLight,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    ...SHADOWS.small,
  },
  accountInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  accountNumber: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.text,
    marginLeft: SPACING.sm,
  },
  accountBank: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginLeft: SPACING.sm,
  },
  accountBalance: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.primary,
  },
  placeholderText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginBottom: SPACING.md,
  },
  accountList: {
    gap: SPACING.sm,
  },
  accountOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    ...SHADOWS.small,
  },
  input: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.md,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.lg,
    ...TYPOGRAPHY.body,
    color: COLORS.text,
  },
  contactButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.surfaceLight,
    marginTop: SPACING.md,
  },
  contactButtonText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.primary,
    fontWeight: '600',
    marginLeft: SPACING.sm,
  },
  amountInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.md,
  },
  currencySymbol: {
    ...TYPOGRAPHY.h2,
    fontWeight: '700',
    color: COLORS.text,
    paddingHorizontal: SPACING.md,
  },
  amountInput: {
    flex: 1,
    paddingVertical: SPACING.lg,
    ...TYPOGRAPHY.h2,
    fontWeight: '700',
    color: COLORS.text,
  },
  paymentModeContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
  },
  paymentModeOption: {
    flex: 1,
    backgroundColor: COLORS.surface,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    alignItems: 'center',
    ...SHADOWS.small,
  },
  paymentModeSelected: {
    borderColor: COLORS.primary,
    borderWidth: 2,
    backgroundColor: COLORS.primaryLight,
  },
  paymentModeText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginTop: SPACING.xs,
  },
  paymentModeTextSelected: {
    color: COLORS.primary,
    fontWeight: '600',
  },
  paymentModeDescription: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    marginTop: SPACING.xs,
    textAlign: 'center',
  },
  descriptionInput: {
    textAlignVertical: 'top',
    height: 100,
  },
  proceedButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    padding: SPACING.lg,
    borderRadius: BORDER_RADIUS.lg,
    marginTop: SPACING.xl,
  },
  proceedButtonText: {
    ...TYPOGRAPHY.button,
    color: COLORS.textOnDark,
    marginRight: SPACING.sm,
  },
  securityFeatures: {
    marginTop: SPACING.xxl,
  },
  securityFeaturesTitle: {
    ...TYPOGRAPHY.h4,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
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
  },
});

export default TransactionInitiateScreen;