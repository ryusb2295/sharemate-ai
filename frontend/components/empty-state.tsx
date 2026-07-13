import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import type { ComponentProps } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { AppButton } from '@/components/app-button';
import { Radius, Spacing } from '@/constants/theme';
import { useRoomTheme } from '@/hooks/use-room-theme';

type IconName = ComponentProps<typeof MaterialIcons>['name'];
export function EmptyState({ title, description, icon = 'inbox', actionLabel, onAction }: { title: string; description: string; icon?: IconName; actionLabel?: string; onAction?: () => void }) {
  const colors = useRoomTheme();
  return (
    <View style={styles.container}>
      <View style={[styles.icon, { backgroundColor: colors.primarySoft }]}><MaterialIcons color={colors.primary} name={icon} size={26} /></View>
      <Text style={[styles.title, { color: colors.textPrimary }]}>{title}</Text>
      <Text style={[styles.description, { color: colors.textSecondary }]}>{description}</Text>
      {actionLabel && onAction ? <AppButton fullWidth={false} label={actionLabel} onPress={onAction} variant="secondary" /> : null}
    </View>
  );
}
const styles = StyleSheet.create({
  container: { alignItems: 'center', paddingVertical: Spacing.section },
  icon: { alignItems: 'center', borderRadius: Radius.card, height: 52, justifyContent: 'center', marginBottom: Spacing.item, width: 52 },
  title: { fontSize: 16, fontWeight: '700', marginBottom: 6 },
  description: { fontSize: 13, lineHeight: 19, marginBottom: Spacing.item, maxWidth: 280, textAlign: 'center' },
});
