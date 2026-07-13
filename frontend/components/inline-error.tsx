import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { StyleSheet, Text, View } from 'react-native';

import { Spacing } from '@/constants/theme';
import { useRoomTheme } from '@/hooks/use-room-theme';

export function InlineError({ message }: { message: string }) {
  const colors = useRoomTheme();
  return (
    <View accessibilityLiveRegion="polite" style={styles.row}>
      <MaterialIcons color={colors.danger} name="error-outline" size={16} />
      <Text style={[styles.text, { color: colors.danger }]}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { alignItems: 'flex-start', flexDirection: 'row', gap: Spacing.compact },
  text: { flex: 1, fontSize: 12, lineHeight: 17 },
});
