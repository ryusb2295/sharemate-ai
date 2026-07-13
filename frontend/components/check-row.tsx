import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Spacing } from '@/constants/theme';
import { useRoomTheme } from '@/hooks/use-room-theme';

type CheckRowProps = { checked: boolean; label: string; detail?: string; disabled?: boolean; onToggle: () => void };

export function CheckRow({ checked, label, detail, disabled = false, onToggle }: CheckRowProps) {
  const colors = useRoomTheme();
  return (
    <Pressable
      accessibilityRole="checkbox"
      accessibilityState={{ checked, disabled }}
      disabled={disabled}
      onPress={onToggle}
      style={({ pressed }) => [styles.row, pressed && { backgroundColor: colors.background }, disabled && styles.disabled]}>
      <MaterialIcons color={checked ? colors.success : colors.placeholder} name={checked ? 'check-circle' : 'radio-button-unchecked'} size={25} />
      <View style={styles.copy}>
        <Text style={[styles.label, { color: checked ? colors.textSecondary : colors.textPrimary }, checked && styles.checked]}>{label}</Text>
        {detail ? <Text style={[styles.detail, { color: colors.textSecondary }]}>{detail}</Text> : null}
      </View>
      <Text style={[styles.state, { color: checked ? colors.success : colors.textSecondary }]}>{checked ? '완료' : '미완료'}</Text>
    </Pressable>
  );
}
const styles = StyleSheet.create({
  row: { alignItems: 'center', flexDirection: 'row', gap: Spacing.md, minHeight: 68, paddingVertical: 10 },
  copy: { flex: 1, gap: 3 },
  label: { fontSize: 15, fontWeight: '600' },
  checked: { textDecorationLine: 'line-through' },
  detail: { fontSize: 12, lineHeight: 17 },
  state: { fontSize: 12, fontWeight: '700' },
  disabled: { opacity: 0.6 },
});
