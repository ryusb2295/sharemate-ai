import { Link } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { AppButton } from '@/components/app-button';
import { AppTextField } from '@/components/app-text-field';
import { InlineError } from '@/components/inline-error';
import { PasswordField } from '@/components/password-field';
import { Layout, Spacing, Typography } from '@/constants/theme';
import { useAuth } from '@/contexts/auth-context';
import { useRoomTheme } from '@/hooks/use-room-theme';
import { apiRequest } from '@/services/api';
import type { AuthResponse } from '@/types/api';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function LoginScreen() {
  const colors = useRoomTheme();
  const { saveAuth } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [emailTouched, setEmailTouched] = useState(false);
  const [passwordTouched, setPasswordTouched] = useState(false);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const normalizedEmail = email.trim().toLowerCase();
  const emailError = emailTouched && !normalizedEmail ? '이메일을 입력해주세요.' : emailTouched && !EMAIL_PATTERN.test(normalizedEmail) ? '올바른 이메일 형식으로 입력해주세요.' : null;
  const passwordError = passwordTouched && !password ? '비밀번호를 입력해주세요.' : requestError;
  const canSubmit = EMAIL_PATTERN.test(normalizedEmail) && password.length > 0 && !loading;

  const login = async () => {
    setEmailTouched(true);
    setPasswordTouched(true);
    if (!canSubmit) return;
    setLoading(true);
    setRequestError(null);
    setNotice(null);
    try {
      const auth = await apiRequest<AuthResponse>('/auth/login', { method: 'POST', body: { email: normalizedEmail, password } });
      await saveAuth(auth);
    } catch (error) {
      setRequestError(error instanceof Error ? error.message : '로그인하지 못했습니다. 입력 정보를 확인해주세요.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.surface }]}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.flex}>
        <ScrollView contentContainerStyle={styles.content} keyboardDismissMode="interactive" keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
          <View style={styles.brandRow}>
            <View style={[styles.brandMark, { backgroundColor: colors.primary }]}><Text style={styles.brandInitial}>R</Text></View>
            <Text style={[styles.brandName, { color: colors.textPrimary }]}>RoomSync</Text>
          </View>

          <View style={styles.heading}>
            <Text style={[Typography.screenTitle, { color: colors.textPrimary }]}>다시 만나서 반가워요</Text>
            <Text style={[styles.description, { color: colors.textSecondary }]}>하우스 생활을 한곳에서 관리하세요</Text>
          </View>

          <View style={styles.form}>
            <AppTextField
              autoCapitalize="none"
              autoComplete="email"
              error={emailError}
              keyboardType="email-address"
              label="이메일"
              onBlur={() => setEmailTouched(true)}
              onChangeText={(value) => { setEmail(value); setRequestError(null); }}
              placeholder="name@example.com"
              returnKeyType="next"
              textContentType="emailAddress"
              value={email}
            />
            <PasswordField
              autoComplete="current-password"
              error={passwordError}
              label="비밀번호"
              onBlur={() => setPasswordTouched(true)}
              onChangeText={(value) => { setPassword(value); setRequestError(null); }}
              onSubmitEditing={login}
              placeholder="비밀번호 입력"
              returnKeyType="done"
              textContentType="password"
              value={password}
            />
            <Pressable accessibilityRole="button" onPress={() => setNotice('비밀번호 찾기는 준비 중입니다.')} style={styles.forgot}>
              <Text style={[styles.link, { color: colors.primary }]}>비밀번호를 잊으셨나요?</Text>
            </Pressable>
            {notice ? <InlineError message={notice} /> : null}
            <AppButton disabled={!canSubmit} label="로그인" loading={loading} onPress={login} />
          </View>

          <Text style={[styles.footer, { color: colors.textSecondary }]}>계정이 없나요? <Link href="/signup" style={[styles.link, { color: colors.primary }]}>회원가입</Link></Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1 }, flex: { flex: 1 },
  content: { flexGrow: 1, paddingBottom: 32, paddingHorizontal: Layout.screenPadding, paddingTop: 30 },
  brandRow: { alignItems: 'center', flexDirection: 'row', gap: 10 },
  brandMark: { alignItems: 'center', borderRadius: 9, height: 34, justifyContent: 'center', width: 34 },
  brandInitial: { color: '#FFFFFF', fontSize: 18, fontWeight: '900' },
  brandName: { fontSize: 20, fontWeight: '800', letterSpacing: -0.3 },
  heading: { gap: Spacing.compact, marginBottom: 36, marginTop: 56 },
  description: { fontSize: 16, lineHeight: 23 },
  form: { gap: Spacing.item },
  forgot: { alignSelf: 'flex-end', minHeight: 36, justifyContent: 'center', marginTop: -8 },
  link: { fontSize: 14, fontWeight: '700' },
  footer: { fontSize: 14, marginTop: 30, textAlign: 'center' },
});
