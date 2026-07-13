import type { PropsWithChildren } from 'react';
import { StyleSheet, View, type ViewProps } from 'react-native';

import { Layout, Radius } from '@/constants/theme';
import { useRoomTheme } from '@/hooks/use-room-theme';

export function RoomCard({ children, style, ...props }: PropsWithChildren<ViewProps>) {
  const colors = useRoomTheme();

  return (
    <View
      style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.border }, style]}
      {...props}>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: Radius.lg,
    borderWidth: 1,
    padding: Layout.cardPadding,
  },
});
