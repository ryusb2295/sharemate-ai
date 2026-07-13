import type { ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { Spacing, Typography } from '@/constants/theme';
import { useRoomTheme } from '@/hooks/use-room-theme';

export function ScreenHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  const colors = useRoomTheme();
  return (
    <View style={styles.row}>
      <View style={styles.copy}>
        <Text style={[Typography.screenTitle, { color: colors.textPrimary }]}>{title}</Text>
        {subtitle ? <Text style={[styles.subtitle, { color: colors.textSecondary }]}>{subtitle}</Text> : null}
      </View>
      {action}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { alignItems: 'flex-start', flexDirection: 'row', gap: Spacing.item, justifyContent: 'space-between' },
  copy: { flex: 1, gap: Spacing.compact },
  subtitle: { fontSize: 15, lineHeight: 22 },
});
