import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { StyleSheet, Text, View } from 'react-native';

import { Radius, Spacing } from '@/constants/theme';
import { useRoomTheme } from '@/hooks/use-room-theme';

type BadgeTone = 'pending' | 'completed' | 'info' | 'danger';

export function StatusBadge({ label, tone }: { label: string; tone: BadgeTone }) {
  const colors = useRoomTheme();
  const palette = {
    pending: { background: colors.warningSoft, foreground: colors.warning, icon: 'schedule' as const },
    completed: { background: colors.successSoft, foreground: colors.success, icon: 'check-circle' as const },
    info: { background: colors.primarySoft, foreground: colors.primary, icon: 'info' as const },
    danger: { background: colors.dangerSoft, foreground: colors.danger, icon: 'error' as const },
  }[tone];
  return (
    <View style={[styles.badge, { backgroundColor: palette.background }]}>
      <MaterialIcons color={palette.foreground} name={palette.icon} size={13} />
      <Text style={[styles.label, { color: palette.foreground }]}>{label}</Text>
    </View>
  );
}
const styles = StyleSheet.create({
  badge: { alignItems: 'center', alignSelf: 'flex-start', borderRadius: Radius.pill, flexDirection: 'row', gap: 4, paddingHorizontal: Spacing.compact, paddingVertical: 5 },
  label: { fontSize: 11, fontWeight: '700' },
});
