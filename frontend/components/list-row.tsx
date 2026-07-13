import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import type { ComponentProps, ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Radius, Spacing } from '@/constants/theme';
import { useRoomTheme } from '@/hooks/use-room-theme';

type IconName = ComponentProps<typeof MaterialIcons>['name'];
type Props = { title: string; subtitle?: string; icon?: IconName; trailing?: ReactNode; onPress?: () => void; destructive?: boolean };

export function ListRow({ title, subtitle, icon, trailing, onPress, destructive = false }: Props) {
  const colors = useRoomTheme();
  const content = (
    <>
      {icon ? <View style={[styles.iconBox, { backgroundColor: destructive ? colors.dangerSoft : colors.primarySoft }]}><MaterialIcons color={destructive ? colors.danger : colors.primary} name={icon} size={21} /></View> : null}
      <View style={styles.copy}>
        <Text style={[styles.title, { color: destructive ? colors.danger : colors.textPrimary }]}>{title}</Text>
        {subtitle ? <Text style={[styles.subtitle, { color: colors.textSecondary }]}>{subtitle}</Text> : null}
      </View>
      {trailing ?? (onPress ? <MaterialIcons color={colors.placeholder} name="chevron-right" size={23} /> : null)}
    </>
  );
  return onPress ? (
    <Pressable accessibilityRole="button" onPress={onPress} style={({ pressed }) => [styles.row, pressed && { backgroundColor: colors.background }]}>{content}</Pressable>
  ) : <View style={styles.row}>{content}</View>;
}

const styles = StyleSheet.create({
  row: { alignItems: 'center', flexDirection: 'row', gap: Spacing.md, minHeight: 64, paddingVertical: 10 },
  iconBox: { alignItems: 'center', borderRadius: Radius.input, height: 40, justifyContent: 'center', width: 40 },
  copy: { flex: 1, gap: 3 },
  title: { fontSize: 15, fontWeight: '600' },
  subtitle: { fontSize: 13, lineHeight: 18 },
});
