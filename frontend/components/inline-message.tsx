import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { StyleSheet, Text, View } from 'react-native';

import { Radius, Spacing } from '@/constants/theme';
import { useRoomTheme } from '@/hooks/use-room-theme';

export function InlineMessage({ message }: { message: string }) {
  const colors = useRoomTheme();

  return (
    <View style={[styles.container, { backgroundColor: colors.dangerSoft }]}>
      <MaterialIcons color={colors.danger} name="error-outline" size={20} />
      <Text style={[styles.message, { color: colors.danger }]}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'flex-start',
    borderRadius: Radius.md,
    flexDirection: 'row',
    gap: Spacing.sm,
    padding: Spacing.md,
  },
  message: {
    flex: 1,
    fontSize: 13,
    lineHeight: 19,
  },
});
