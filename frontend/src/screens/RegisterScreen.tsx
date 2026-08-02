// src/screens/RegisterScreen.tsx
// ─────────────────────────────────────────────────────────────────────────────
// SecureWealth Twin — Open an account
//
// Two stages in one screen:
//   1. FORM     — details + MPIN, validated inline before submit
//   2. ID CARD  — the issued SecureWealth ID presented like a bank welcome
//                 letter, because it is the customer's permanent login
//                 credential and they only see it once here.
//
// Backend: POST /api/v1/auth/register → { message, user_id, customer_id }
// ─────────────────────────────────────────────────────────────────────────────

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Alert,
  Share,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { COLORS } from '../constants/colors';
import { useI18n } from '../i18n';
import { SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../constants/theme';
import { api, ApiError } from '../api/apiService';

// ── Validation ────────────────────────────────────────────────────────────────
type Errors = Partial<Record<'full_name' | 'phone' | 'email' | 'dob' | 'mpin' | 'confirm', string>>;

const DOB_RE = /^\d{4}-\d{2}-\d{2}$/;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validate(f: {
  full_name: string; phone: string; email: string; dob: string; mpin: string; confirm: string;
}): Errors {
  const e: Errors = {};
  if (f.full_name.trim().length < 3) e.full_name = 'Please enter your full name.';
  if (!/^\d{10,15}$/.test(f.phone)) e.phone = 'Enter a valid mobile number (10–15 digits).';
  if (f.email && !EMAIL_RE.test(f.email)) e.email = 'That email address does not look right.';
  if (f.dob && !DOB_RE.test(f.dob)) e.dob = 'Use the format YYYY-MM-DD.';
  if (!/^\d{6}$/.test(f.mpin)) e.mpin = 'Your MPIN must be exactly 6 digits.';
  else if (/^(\d)\1{5}$/.test(f.mpin)) e.mpin = 'Avoid repeating the same digit six times.';
  else if ('0123456789'.includes(f.mpin) || '9876543210'.includes(f.mpin))
    e.mpin = 'Avoid a sequence like 123456.';
  if (f.confirm !== f.mpin) e.confirm = 'The two MPINs do not match.';
  return e;
}

// ── Reusable field ────────────────────────────────────────────────────────────
const Field = ({
  label, icon, error, hint, children,
}: {
  label: string; icon: string; error?: string; hint?: string; children: React.ReactNode;
}) => (
  <View style={styles.field}>
    <View style={styles.labelRow}>
      <Feather name={icon as any} size={13} color={COLORS.textSecondary} />
      <Text style={styles.label}>{label}</Text>
    </View>
    <View style={[styles.inputWrap, error ? styles.inputWrapError : null]}>{children}</View>
    {error ? (
      <View style={styles.errorRow}>
        <Feather name="alert-circle" size={12} color={COLORS.danger} />
        <Text style={styles.errorText}>{error}</Text>
      </View>
    ) : hint ? (
      <Text style={styles.hint}>{hint}</Text>
    ) : null}
  </View>
);

// ── Screen ────────────────────────────────────────────────────────────────────
const RegisterScreen = ({ navigation, route }: any) => {
  const { t } = useI18n();
  const insets = useSafeAreaInsets();
  const onRegistered = route?.params?.onRegistered;

  const [form, setForm] = useState({
    full_name: '', phone: '', email: '', dob: '', mpin: '', confirm: '',
  });
  const [errors, setErrors] = useState<Errors>({});
  const [submitting, setSubmitting] = useState(false);
  const [customerId, setCustomerId] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const set = (k: keyof typeof form) => (v: string) =>
    setForm((p) => ({ ...p, [k]: v }));

  const handleSubmit = async () => {
    const e = validate(form);
    setErrors(e);
    if (Object.keys(e).length > 0) return;

    setSubmitting(true);
    try {
      const res = await api.register({
        full_name: form.full_name.trim(),
        phone: form.phone,
        email: form.email.trim() || undefined,
        date_of_birth: form.dob || undefined,
        mpin: form.mpin,
      });
      setCustomerId(res.customer_id ?? null);
    } catch (err) {
      const msg =
        err instanceof ApiError && err.isConnectivityError
          ? 'Cannot reach the server. Check your connection and try again.'
          : err instanceof ApiError
          ? err.message
          : 'Registration could not be completed. Please try again.';
      Alert.alert('Registration failed', msg);
    } finally {
      setSubmitting(false);
    }
  };

  const shareId = async () => {
    if (!customerId) return;
    try {
      await Share.share({
        message:
          `My SecureWealth ID is ${customerId}. ` +
          `I use it to sign in to the SecureWealth Twin app.`,
      });
    } catch {
      /* user dismissed */
    }
  };

  // ══ STAGE 2 — the issued ID ═════════════════════════════════════════════════
  if (customerId) {
    return (
      <ScrollView
        style={styles.container}
        contentContainerStyle={[styles.content, { paddingTop: insets.top + SPACING.xl }]}
      >
        <View style={styles.successIcon}>
          <Feather name="check" size={34} color={COLORS.textOnDark} />
        </View>
        <Text style={styles.successTitle}>{t('register.welcome')}</Text>
        <Text style={styles.successSub}>{t('register.yourIdIs')}</Text>

        {/* The ID, presented like a bank card */}
        <View style={styles.idCard}>
          <View style={styles.idCardTop}>
            <Feather name="shield" size={16} color={COLORS.accent} />
            <Text style={styles.idCardBrand}>SecureWealth ID</Text>
          </View>
          <Text style={styles.idValue} selectable>
            {customerId}
          </Text>
          <Text style={styles.idCardName}>{form.full_name.trim().toUpperCase()}</Text>
        </View>

        <TouchableOpacity style={styles.ghostBtn} onPress={shareId} activeOpacity={0.8}>
          <Feather name="share-2" size={15} color={COLORS.primary} />
          <Text style={styles.ghostBtnText}>{t('register.saveShare')}</Text>
        </TouchableOpacity>

        <View style={styles.noticeCard}>
          <Feather name="alert-triangle" size={15} color="#B45309" />
          <Text style={styles.noticeText}>
            Write this down before continuing. You will need your SecureWealth ID
            every time you sign in — your mobile number will not work.
          </Text>
        </View>

        <TouchableOpacity
          style={styles.checkRow}
          onPress={() => setSaved((s) => !s)}
          activeOpacity={0.7}
        >
          <View style={[styles.checkbox, saved && styles.checkboxOn]}>
            {saved && <Feather name="check" size={13} color={COLORS.textOnDark} />}
          </View>
          <Text style={styles.checkLabel}>{t('register.savedId')}</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.primaryBtn, !saved && styles.primaryBtnDisabled]}
          disabled={!saved}
          onPress={() => {
            if (onRegistered) onRegistered(customerId);
            navigation.goBack();
          }}
          activeOpacity={0.85}
        >
          <Text style={styles.primaryBtnText}>{t('register.continueSignIn')}</Text>
          <Feather name="arrow-right" size={18} color={COLORS.textOnDark} />
        </TouchableOpacity>
      </ScrollView>
    );
  }

  // ══ STAGE 1 — the form ══════════════════════════════════════════════════════
  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        contentContainerStyle={[styles.content, { paddingTop: insets.top + SPACING.lg }]}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <TouchableOpacity
          style={styles.backBtn}
          onPress={() => navigation.goBack()}
          activeOpacity={0.7}
          hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
          accessibilityRole="button"
          accessibilityLabel={t('common.back')}
        >
          <Feather name="arrow-left" size={20} color={COLORS.text} />
        </TouchableOpacity>

        <Text style={styles.title}>{t('register.title')}</Text>
        <Text style={styles.subtitle}>
          A few details and you're set. We'll issue your SecureWealth ID at the end.
        </Text>

        <Field label={t('register.fullName')} icon="user" error={errors.full_name}>
          <TextInput
            style={styles.input}
            value={form.full_name}
            onChangeText={set('full_name')}
            placeholder={t('register.subtitle')}
            placeholderTextColor={COLORS.textTertiary}
            autoCapitalize="words"
            returnKeyType="next"
          />
        </Field>

        <Field
          label={t('register.phone')}
          icon="smartphone"
          error={errors.phone}
          hint="Used for alerts and one-time passwords — not for signing in."
        >
          <TextInput
            style={styles.input}
            value={form.phone}
            onChangeText={(t) => set('phone')(t.replace(/[^\d]/g, '').slice(0, 15))}
            placeholder="10-digit mobile number"
            placeholderTextColor={COLORS.textTertiary}
            keyboardType="number-pad"
          />
        </Field>

        <Field label={t('register.emailOpt')} icon="mail" error={errors.email}>
          <TextInput
            style={styles.input}
            value={form.email}
            onChangeText={set('email')}
            placeholder="you@example.com"
            placeholderTextColor={COLORS.textTertiary}
            keyboardType="email-address"
            autoCapitalize="none"
          />
        </Field>

        <Field
          label={t('register.dobOpt')}
          icon="calendar"
          error={errors.dob}
          hint="We may ask for this to verify a high-value investment."
        >
          <TextInput
            style={styles.input}
            value={form.dob}
            onChangeText={(t) => set('dob')(t.replace(/[^\d-]/g, '').slice(0, 10))}
            placeholder="YYYY-MM-DD"
            placeholderTextColor={COLORS.textTertiary}
            keyboardType="numbers-and-punctuation"
          />
        </Field>

        <View style={styles.divider} />

        <Field
          label={t('register.mpin')}
          icon="lock"
          error={errors.mpin}
          hint="Avoid birthdays, repeated digits and sequences."
        >
          <TextInput
            style={[styles.input, styles.pinInput]}
            value={form.mpin}
            onChangeText={(t) => set('mpin')(t.replace(/[^\d]/g, '').slice(0, 6))}
            placeholder="••••••"
            placeholderTextColor={COLORS.textTertiary}
            keyboardType="number-pad"
            secureTextEntry
            maxLength={6}
          />
        </Field>

        <Field label={t('register.confirmMpin')} icon="check-circle" error={errors.confirm}>
          <TextInput
            style={[styles.input, styles.pinInput]}
            value={form.confirm}
            onChangeText={(t) => set('confirm')(t.replace(/[^\d]/g, '').slice(0, 6))}
            placeholder="••••••"
            placeholderTextColor={COLORS.textTertiary}
            keyboardType="number-pad"
            secureTextEntry
            maxLength={6}
          />
        </Field>

        <TouchableOpacity
          style={[styles.primaryBtn, submitting && styles.primaryBtnDisabled]}
          onPress={handleSubmit}
          disabled={submitting}
          activeOpacity={0.85}
        >
          {submitting ? (
            <ActivityIndicator color={COLORS.textOnDark} />
          ) : (
            <>
              <Feather name="shield" size={17} color={COLORS.textOnDark} />
              <Text style={styles.primaryBtnText}>{t('register.create')}</Text>
            </>
          )}
        </TouchableOpacity>

        <Text style={styles.legal}>
          By continuing you agree to SecureWealth's terms. Your details are used only
          to operate your account and protect it from fraud.
        </Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: SPACING.lg, paddingBottom: SPACING.xxl },

  backBtn: {
    width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center',
    backgroundColor: COLORS.surface, borderWidth: 1, borderColor: COLORS.border,
    marginBottom: SPACING.lg,
  },
  title: { ...TYPOGRAPHY.h1, color: COLORS.text },
  subtitle: {
    ...TYPOGRAPHY.body, color: COLORS.textSecondary,
    marginTop: SPACING.xs, marginBottom: SPACING.xl, lineHeight: 21,
  },

  field: { marginBottom: SPACING.lg },
  labelRow: { flexDirection: 'row', alignItems: 'center', gap: SPACING.xs, marginBottom: SPACING.xs },
  label: {
    ...TYPOGRAPHY.captionBold, color: COLORS.textSecondary,
    textTransform: 'uppercase', letterSpacing: 0.6,
  },
  inputWrap: {
    backgroundColor: COLORS.surface, borderRadius: BORDER_RADIUS.md,
    borderWidth: 1.5, borderColor: COLORS.border, paddingHorizontal: SPACING.md,
  },
  inputWrapError: { borderColor: COLORS.danger },
  input: { ...TYPOGRAPHY.body, color: COLORS.text, paddingVertical: SPACING.md },
  pinInput: { letterSpacing: 8, fontSize: 18 },
  errorRow: { flexDirection: 'row', alignItems: 'center', gap: 5, marginTop: 5 },
  errorText: { ...TYPOGRAPHY.caption, color: COLORS.danger, flex: 1 },
  hint: { ...TYPOGRAPHY.caption, color: COLORS.textTertiary, marginTop: 5, lineHeight: 16 },

  divider: { height: 1, backgroundColor: COLORS.border, marginBottom: SPACING.lg },

  primaryBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: SPACING.sm,
    backgroundColor: COLORS.primary, borderRadius: BORDER_RADIUS.lg,
    paddingVertical: SPACING.md + 2, marginTop: SPACING.sm, ...SHADOWS.medium,
  },
  primaryBtnDisabled: { opacity: 0.45 },
  primaryBtnText: { ...TYPOGRAPHY.bodyMedium, color: COLORS.textOnDark, fontSize: 16 },

  legal: {
    ...TYPOGRAPHY.caption, color: COLORS.textTertiary,
    textAlign: 'center', marginTop: SPACING.lg, lineHeight: 17,
  },

  // ── Success stage ──
  successIcon: {
    width: 72, height: 72, borderRadius: 36, alignSelf: 'center',
    backgroundColor: COLORS.success, alignItems: 'center', justifyContent: 'center',
    marginBottom: SPACING.lg, ...SHADOWS.medium,
  },
  successTitle: { ...TYPOGRAPHY.h1, color: COLORS.text, textAlign: 'center' },
  successSub: {
    ...TYPOGRAPHY.body, color: COLORS.textSecondary, textAlign: 'center',
    marginTop: SPACING.xs, marginBottom: SPACING.xl,
  },

  idCard: {
    backgroundColor: COLORS.primaryDark, borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg, ...SHADOWS.large,
  },
  idCardTop: { flexDirection: 'row', alignItems: 'center', gap: SPACING.xs },
  idCardBrand: {
    ...TYPOGRAPHY.caption, color: '#D4AF37',
    textTransform: 'uppercase', letterSpacing: 1.2, fontWeight: '700',
  },
  idValue: {
    fontSize: 28, fontWeight: '800', color: COLORS.textOnDark,
    letterSpacing: 3, marginTop: SPACING.md,
  },
  idCardName: {
    ...TYPOGRAPHY.caption, color: '#A7F3D0',
    marginTop: SPACING.sm, letterSpacing: 1,
  },

  ghostBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: SPACING.xs,
    paddingVertical: SPACING.md, marginTop: SPACING.sm,
  },
  ghostBtnText: { ...TYPOGRAPHY.bodyMedium, color: COLORS.primary },

  noticeCard: {
    flexDirection: 'row', gap: SPACING.sm, backgroundColor: '#FFFBEB',
    borderRadius: BORDER_RADIUS.md, padding: SPACING.md, marginTop: SPACING.sm,
    borderWidth: 1, borderColor: '#FDE68A',
  },
  noticeText: { ...TYPOGRAPHY.caption, color: '#92400E', flex: 1, lineHeight: 17 },

  checkRow: {
    flexDirection: 'row', alignItems: 'center', gap: SPACING.sm,
    marginTop: SPACING.lg, marginBottom: SPACING.md,
  },
  checkbox: {
    width: 22, height: 22, borderRadius: 6, borderWidth: 2,
    borderColor: COLORS.border, alignItems: 'center', justifyContent: 'center',
  },
  checkboxOn: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  checkLabel: { ...TYPOGRAPHY.body, color: COLORS.text, flex: 1 },
});

export default RegisterScreen;
