// src/components/common/HashChainVisual.tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS } from '../../constants/theme';

interface HashChainVisualProps {
  hashes: string[];
  currentHash?: string;
  verifiedIndex?: number;
}

const HashChainVisual: React.FC<HashChainVisualProps> = ({ 
  hashes, 
  currentHash,
  verifiedIndex = -1 
}) => {
  const allHashes = [...hashes];
  if (currentHash) {
    allHashes.push(currentHash);
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Hash Chain Verification</Text>
      <View style={styles.chainContainer}>
        {allHashes.map((hash, index) => (
          <React.Fragment key={index}>
            <View style={[
              styles.hashNode,
              verifiedIndex >= index && styles.verifiedNode,
              verifiedIndex < index && styles.pendingNode,
            ]}>
              <Feather 
                name={verifiedIndex >= index ? 'check-circle' : 'circle'} 
                size={16} 
                color={verifiedIndex >= index ? COLORS.success : COLORS.textTertiary} 
              />
              <Text style={[
                styles.hashText,
                verifiedIndex >= index && styles.verifiedText,
              ]}>
                {hash.substring(0, 8)}...
              </Text>
            </View>
            
            {index < allHashes.length - 1 && (
              <Feather 
                name="arrow-right" 
                size={16} 
                color={COLORS.textTertiary} 
                style={styles.arrow} 
              />
            )}
          </React.Fragment>
        ))}
      </View>
      <Text style={styles.status}>
        {verifiedIndex === -1 ? 'Not verified' : `Verified up to ${verifiedIndex + 1} of ${allHashes.length}`}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: SPACING.lg,
    backgroundColor: COLORS.surfaceLight,
    borderRadius: BORDER_RADIUS.lg,
    marginVertical: SPACING.md,
  },
  title: {
    ...TYPOGRAPHY.bodySm,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  chainContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    flexWrap: 'wrap',
  },
  hashNode: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    paddingHorizontal: SPACING.sm,
    paddingVertical: SPACING.xs,
    borderRadius: BORDER_RADIUS.full,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  verifiedNode: {
    borderColor: COLORS.success,
    backgroundColor: COLORS.success + '10',
  },
  pendingNode: {
    borderColor: COLORS.textTertiary,
  },
  hashText: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textTertiary,
    marginLeft: SPACING.xs,
  },
  verifiedText: {
    color: COLORS.success,
  },
  arrow: {
    marginHorizontal: SPACING.xs,
  },
  status: {
    ...TYPOGRAPHY.caption,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginTop: SPACING.sm,
  },
});

export default HashChainVisual;