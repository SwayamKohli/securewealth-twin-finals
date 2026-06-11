// src/screens/PhishingScannerScreen.tsx
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Alert } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import Card from '../components/common/Card';
import RiskBadge from '../components/common/RiskBadge';

const PhishingScannerScreen = () => {
  const [inputText, setInputText] = useState('');
  const [scanResult, setScanResult] = useState<any>(null);
  const [isScanning, setIsScanning] = useState(false);

  // Mock scan function
  const handleScan = async () => {
    if (!inputText.trim()) {
      Alert.alert('Error', 'Please enter a message or URL to scan');
      return;
    }

    setIsScanning(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Mock scan results based on input
      let result;
      if (inputText.toLowerCase().includes('urgent') && inputText.toLowerCase().includes('click')) {
        result = {
          status: 'PHISHING',
          confidence: 95,
          riskLevel: 'CRITICAL' as const,
          threats: [
            'Creates urgency',
            'Requests sensitive information',
            'Suspicious link detected'
          ],
          explanation: 'This message creates urgency and requests sensitive information, which are common phishing patterns. The included link redirects to a suspicious domain.',
          safetyTips: [
            'Never click links in unsolicited messages',
            'Verify sender identity through official channels',
            'Report suspicious messages to bank'
          ]
        };
      } else if (inputText.toLowerCase().includes('verify') && inputText.toLowerCase().includes('account')) {
        result = {
          status: 'SUSPICIOUS',
          confidence: 78,
          riskLevel: 'HIGH' as const,
          threats: [
            'Requests account verification',
            'Uses official-looking language'
          ],
          explanation: 'This message asks for account verification, which banks typically don\'t request via text. Be cautious of such requests.',
          safetyTips: [
            'Contact bank through official app/website',
            'Don\'t reply to suspicious messages',
            'Block the sender'
          ]
        };
      } else {
        result = {
          status: 'SAFE',
          confidence: 98,
          riskLevel: 'LOW' as const,
          threats: [],
          explanation: 'No suspicious patterns detected in this message. It appears to be legitimate.',
          safetyTips: [
            'Continue practicing good security habits',
            'Be vigilant about unsolicited requests'
          ]
        };
      }

      setScanResult(result);
    } catch (error) {
      console.error('Scan failed:', error);
      Alert.alert('Error', 'Scan failed. Please try again.');
    } finally {
      setIsScanning(false);
    }
  };

  const handlePaste = async () => {
    // In a real app, you'd use Clipboard API
    Alert.alert('Paste', 'Paste functionality would be implemented in the full app');
  };

  const handleHistory = () => {
    console.log('Viewing scan history...');
    // Navigate to scan history
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity>
          <Feather name="arrow-left" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Phishing Scanner</Text>
        <TouchableOpacity onPress={handleHistory}>
          <Feather name="history" size={24} color={COLORS.text} />
        </TouchableOpacity>
      </View>

      {/* Input Card */}
      <Card style={styles.inputCard}>
        <Text style={styles.sectionTitle}>Scan Suspicious Content</Text>
        <Text style={styles.sectionSubtitle}>Paste suspicious messages, URLs, or content to analyze</Text>
        
        <TextInput
          style={styles.textInput}
          placeholder="Paste suspicious message or URL here..."
          value={inputText}
          onChangeText={setInputText}
          multiline
          numberOfLines={6}
          textAlignVertical="top"
        />
        
        <View style={styles.inputActions}>
          <TouchableOpacity style={styles.pasteButton} onPress={handlePaste}>
            <Feather name="clipboard" size={20} color={COLORS.primary} />
            <Text style={styles.pasteButtonText}>Paste</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={[styles.scanButton, isScanning && styles.scanButtonDisabled]}
            onPress={handleScan}
            disabled={isScanning}
          >
            <Feather name={isScanning ? "loader" : "search"} size={20} color={COLORS.textOnDark} />
            <Text style={styles.scanButtonText}>
              {isScanning ? 'Scanning...' : 'Scan for Phishing'}
            </Text>
          </TouchableOpacity>
        </View>
      </Card>

      {/* Results */}
      {scanResult && (
        <Card style={styles.resultCard}>
          <View style={styles.resultHeader}>
            <View style={[
              styles.resultIconContainer,
              { 
                backgroundColor: 
                  scanResult.status === 'PHISHING' ? COLORS.s_danger + '20' : 
                  scanResult.status === 'SUSPICIOUS' ? COLORS.warning + '20' : 
                  COLORS.success + '20'
              }
            ]}>
              {scanResult.status === 'PHISHING' && <Feather name="alert-triangle" size={24} color={COLORS.s_danger} />}
              {scanResult.status === 'SUSPICIOUS' && <Feather name="alert-circle" size={24} color={COLORS.warning} />}
              {scanResult.status === 'SAFE' && <Feather name="shield-check" size={24} color={COLORS.success} />}
            </View>
            
            <View style={styles.resultInfo}>
              <View style={styles.resultStatusRow}>
                {/* <Text style={styles.resultStatus}>{scanResult.status}</Text> */}
                <Text
                style={[
                    styles.resultStatus,
                    {
                    color:
                        scanResult.status === 'PHISHING'
                        ? COLORS.danger
                        : scanResult.status === 'SUSPICIOUS'
                        ? COLORS.warning
                        : COLORS.success,
                    },
                ]}
                >
                {scanResult.status}
                </Text>
                <RiskBadge level={scanResult.riskLevel} showIcon={true} size="sm" />
              </View>
              <Text style={styles.resultConfidence}>Confidence: {scanResult.confidence}%</Text>
            </View>
          </View>

          {/* Threats */}
          {scanResult.threats.length > 0 && (
            <View style={styles.threatsContainer}>
              <Text style={styles.threatsTitle}>Detected Threats:</Text>
              {scanResult.threats.map((threat: string, index: number) => (
                <View key={index} style={styles.threatItem}>
                  <Feather name="x-circle" size={16} color={COLORS.danger} />
                  <Text style={styles.threatText}>{threat}</Text>
                </View>
              ))}
            </View>
          )}

          {/* Explanation */}
          <View style={styles.explanationContainer}>
            <Text style={styles.explanationTitle}>Security Analysis:</Text>
            <Text style={styles.explanationText}>{scanResult.explanation}</Text>
          </View>

          {/* Safety Tips */}
          <View style={styles.tipsContainer}>
            <Text style={styles.tipsTitle}>Safety Tips:</Text>
            {scanResult.safetyTips.map((tip: string, index: number) => (
              <View key={index} style={styles.tipItem}>
                <Feather name="check-circle" size={14} color={COLORS.success} />
                <Text style={styles.tipText}>{tip}</Text>
              </View>
            ))}
          </View>
        </Card>
      )}

      {/* Quick Tips */}
      <Card style={styles.tipsCard}>
        <Text style={styles.tipsTitle}>Common Phishing Patterns</Text>
        <View style={styles.patternsList}>
          <View style={styles.patternItem}>
            <Feather name="alert-triangle" size={16} color={COLORS.danger} />
            <Text style={styles.patternText}>Urgent language ("Act now!", "Immediate action required")</Text>
          </View>
          <View style={styles.patternItem}>
            <Feather name="alert-triangle" size={16} color={COLORS.danger} />
            <Text style={styles.patternText}>Requests for sensitive information (passwords, OTP, account details)</Text>
          </View>
          <View style={styles.patternItem}>
            <Feather name="alert-triangle" size={16} color={COLORS.danger} />
            <Text style={styles.patternText}>Suspicious links or attachments</Text>
          </View>
          <View style={styles.patternItem}>
            <Feather name="alert-triangle" size={16} color={COLORS.danger} />
            <Text style={styles.patternText}>Official-looking sender with fake domain</Text>
          </View>
        </View>
      </Card>

      {/* Security Features */}
      <View style={styles.featuresContainer}>
        <Text style={styles.featuresTitle}>Security Features</Text>
        <View style={styles.featureList}>
          <View style={styles.featureItem}>
            <Feather name="shield" size={20} color={COLORS.primary} />
            <Text style={styles.featureText}>Real-time scanning</Text>
          </View>
          <View style={styles.featureItem}>
            <Feather name="message-square" size={20} color={COLORS.primary} />
            <Text style={styles.featureText}>Message analysis</Text>
          </View>
          <View style={styles.featureItem}>
            <Feather name="link" size={20} color={COLORS.primary} />
            <Text style={styles.featureText}>URL reputation checking</Text>
          </View>
          <View style={styles.featureItem}>
            <Feather name="book-open" size={20} color={COLORS.primary} />
            <Text style={styles.featureText}>Educational safety tips</Text>
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
  inputCard: {
    padding: SPACING.lg,
    marginBottom: SPACING.lg,
  },
  sectionTitle: {
    ...TYPOGRAPHY.h4,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  sectionSubtitle: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginBottom: SPACING.md,
  },
  textInput: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.md,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.lg,
    ...TYPOGRAPHY.body,
    color: COLORS.text,
    textAlignVertical: 'top',
    height: 120,
    marginBottom: SPACING.md,
  },
  inputActions: {
    flexDirection: 'row',
    gap: SPACING.sm,
  },
  pasteButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.surface,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  pasteButtonText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.primary,
    fontWeight: '600',
    marginLeft: SPACING.sm,
  },
  scanButton: {
    flex: 2,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
  },
  scanButtonDisabled: {
    backgroundColor: COLORS.textTertiary,
  },
  scanButtonText: {
    ...TYPOGRAPHY.button,
    color: COLORS.textOnDark,
    marginLeft: SPACING.sm,
  },
  resultCard: {
    padding: SPACING.lg,
    marginBottom: SPACING.lg,
  },
  resultHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  resultIconContainer: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  resultInfo: {
    flex: 1,
  },
  resultStatusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
//   resultStatus: {
//     ...TYPOGRAPHY.h4,
//     fontWeight: '600',
//     color: 
//       scanResult?.status === 'PHISHING' ? COLORS.danger : 
//       scanResult?.status === 'SUSPICIOUS' ? COLORS.warning : 
//       COLORS.success,
//   },
  resultStatus: {
  ...TYPOGRAPHY.h4,
  fontWeight: '600',
},
  resultConfidence: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.textSecondary,
    marginTop: SPACING.xs,
  },
  threatsContainer: {
    marginBottom: SPACING.md,
  },
  threatsTitle: {
    ...TYPOGRAPHY.bodySm,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  threatItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.danger + '10',
    padding: SPACING.sm,
    borderRadius: BORDER_RADIUS.sm,
    marginBottom: SPACING.xs,
  },
  threatText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.danger,
    marginLeft: SPACING.sm,
  },
  explanationContainer: {
    marginBottom: SPACING.md,
  },
  explanationTitle: {
    ...TYPOGRAPHY.bodySm,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  explanationText: {
    ...TYPOGRAPHY.body,
    color: COLORS.text,
    lineHeight: 20,
  },
  tipsContainer: {
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    paddingTop: SPACING.md,
  },
  tipsTitle: {
    ...TYPOGRAPHY.bodySm,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  tipItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: SPACING.xs,
  },
  tipText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.success,
    marginLeft: SPACING.sm,
    flex: 1,
  },
  tipsCard: {
    padding: SPACING.lg,
    marginBottom: SPACING.lg,
  },
  patternsList: {
    gap: SPACING.sm,
  },
  patternItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  patternText: {
    ...TYPOGRAPHY.bodySm,
    color: COLORS.danger,
    marginLeft: SPACING.sm,
    flex: 1,
  },
  featuresContainer: {
    marginTop: SPACING.xxl,
  },
  featuresTitle: {
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

export default PhishingScannerScreen;