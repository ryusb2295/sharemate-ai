import type { PropsWithChildren, ReactNode } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ScreenHeader } from '@/components/screen-header';
import { Layout, Spacing } from '@/constants/theme';
import { useRoomTheme } from '@/hooks/use-room-theme';

type ScreenContainerProps = PropsWithChildren<{
  title: string;
  subtitle?: string;
  headerAction?: ReactNode;
  keyboardAware?: boolean;
}>;

export function ScreenContainer({ children, title, subtitle, headerAction, keyboardAware = false }: ScreenContainerProps) {
  const colors = useRoomTheme();
  const content = (
    <ScrollView
      contentInsetAdjustmentBehavior="automatic"
      contentContainerStyle={styles.content}
      keyboardDismissMode="interactive"
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}>
      <ScreenHeader action={headerAction} subtitle={subtitle} title={title} />
      <View style={styles.body}>{children}</View>
    </ScrollView>
  );

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.background }]} edges={['top']}>
      {keyboardAware ? <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.flex}>{content}</KeyboardAvoidingView> : content}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1 },
  flex: { flex: 1 },
  content: { flexGrow: 1, paddingBottom: 40, paddingHorizontal: Layout.screenPadding, paddingTop: Spacing.item },
  body: { gap: Spacing.section, marginTop: Spacing.section },
});
