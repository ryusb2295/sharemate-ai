import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { Radius, Spacing } from '@/constants/theme';
import { useRoomTheme } from '@/hooks/use-room-theme';

export function LoadingOverlay({ visible, label = '불러오는 중' }: { visible: boolean; label?: string }) {
  const colors = useRoomTheme();
  if (!visible) return null;
  return (
    <View accessibilityLiveRegion="polite" style={styles.overlay}>
      <View style={[styles.panel, { backgroundColor: colors.surface, borderColor: colors.border }]}>
        <ActivityIndicator color={colors.primary} />
        <Text style={[styles.label, { color: colors.textPrimary }]}>{label}</Text>
      </View>
    </View>
  );
}
const styles = StyleSheet.create({
  overlay: { ...StyleSheet.absoluteFillObject, alignItems: 'center', backgroundColor: 'rgba(17,24,39,0.18)', justifyContent: 'center', zIndex: 20 },
  panel: { alignItems: 'center', borderRadius: Radius.card, borderWidth: 1, flexDirection: 'row', gap: Spacing.md, paddingHorizontal: Spacing.xl, paddingVertical: Spacing.item },
  label: { fontSize: 14, fontWeight: '600' },
});
