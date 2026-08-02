// src/components/ErrorBoundary.tsx
// ─────────────────────────────────────────────────────────────────────────────
// Catches render errors anywhere below it and shows a recoverable screen
// instead of React Native's white screen of death (M7, task 21).
//
// Why this matters more in a banking app than elsewhere: a customer who sees a
// blank screen mid-investment does not know whether their money moved. The
// fallback below answers that question first, before anything else.
//
// Class component by necessity — React has no hook equivalent of
// componentDidCatch.
// ─────────────────────────────────────────────────────────────────────────────

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { Feather } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS } from '../constants/theme';
// A class component cannot use the useI18n hook, and this must keep working
// even when the React tree below it has already failed — so read the stored
// language directly rather than depending on the provider.
import { CATALOGS, type Language } from '../i18n/translations';

type Props = { children: React.ReactNode };
type State = { error: Error | null; lang: Language };

class ErrorBoundary extends React.Component<Props, State> {
  state: State = { error: null, lang: 'en' };

  componentDidMount() {
    // Best-effort: if this fails we simply show English.
    import('@react-native-async-storage/async-storage')
      .then(({ default: storage }) => storage.getItem('swt_language'))
      .then((v) => {
        if (v === 'hi' || v === 'pa') this.setState({ lang: v });
      })
      .catch(() => undefined);
  }

  t = (key: string): string =>
    CATALOGS[this.state.lang]?.[key] ?? CATALOGS.en[key] ?? key;

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Kept to console rather than shipped anywhere: crash payloads can contain
    // account data, and this app has no scrubbed telemetry pipeline.
    console.error('Unhandled UI error:', error, info?.componentStack);
  }

  reset = () => this.setState({ error: null });

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;

    return (
      <ScrollView contentContainerStyle={styles.root}>
        <View style={styles.iconWrap}>
          <Feather name="alert-triangle" size={30} color={COLORS.caution} />
        </View>

        <Text style={styles.title}>{this.t('error.title')}</Text>

        {/* The first thing a customer needs to know. */}
        <View style={styles.assurance}>
          <Feather name="lock" size={15} color={COLORS.primaryDark} />
          <Text style={styles.assuranceText}>{this.t('error.assurance')}</Text>
        </View>

        <Text style={styles.body}>{this.t('error.body')}</Text>

        <TouchableOpacity style={styles.btn} onPress={this.reset} activeOpacity={0.85}>
          <Feather name="refresh-cw" size={15} color={COLORS.textOnDark} />
          <Text style={styles.btnText}>{this.t('common.tryAgain')}</Text>
        </TouchableOpacity>

        {__DEV__ && (
          <View style={styles.devBox}>
            <Text style={styles.devLabel}>Developer detail (debug builds only)</Text>
            <Text style={styles.devText}>{String(error?.message || error)}</Text>
          </View>
        )}
      </ScrollView>
    );
  }
}

const styles = StyleSheet.create({
  root: {
    flexGrow: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.background,
    padding: SPACING.xl,
  },
  iconWrap: {
    width: 62,
    height: 62,
    borderRadius: 20,
    backgroundColor: '#FEF3C7',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: SPACING.lg,
  },
  title: { ...TYPOGRAPHY.h3, color: COLORS.text, textAlign: 'center' },
  assurance: {
    flexDirection: 'row',
    gap: SPACING.sm,
    backgroundColor: COLORS.primaryVeryLight,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginTop: SPACING.lg,
  },
  assuranceText: {
    ...TYPOGRAPHY.caption,
    color: COLORS.primaryDark,
    flex: 1,
    lineHeight: 17,
    fontWeight: '600',
  },
  body: {
    ...TYPOGRAPHY.body,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginTop: SPACING.lg,
    lineHeight: 21,
  },
  btn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.sm,
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.lg,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.xl,
    marginTop: SPACING.xl,
  },
  btnText: { ...TYPOGRAPHY.bodyMedium, color: COLORS.textOnDark, fontWeight: '700' },
  devBox: {
    marginTop: SPACING.xl,
    padding: SPACING.md,
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.md,
    borderWidth: 1,
    borderColor: COLORS.border,
    width: '100%',
  },
  devLabel: { ...TYPOGRAPHY.caption, color: COLORS.textTertiary, marginBottom: 4 },
  devText: { ...TYPOGRAPHY.caption, color: COLORS.danger, fontFamily: 'monospace' },
});

export default ErrorBoundary;
