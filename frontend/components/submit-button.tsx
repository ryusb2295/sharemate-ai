import { ActivityIndicator, Pressable, StyleSheet, Text } from 'react-native';

import { Radius, Spacing } from '@/constants/theme';
import { useRoomTheme } from '@/hooks/use-room-theme';

type SubmitButtonProps = {
  label: string;
  loading?: boolean;
  disabled?: boolean;
  onPress: () => void;
};

export function SubmitButton({ label, loading = false, disabled = false, onPress }: SubmitButtonProps) {
  const colors = useRoomTheme();
  const unavailable = disabled || loading;

  return (
    <Pressable
      accessibilityRole="button"
      disabled={unavailable}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        { backgroundColor: pressed ? colors.primaryPressed : colors.primary },
        unavailable && styles.disabled,
      ]}>
      {loading ? (
        <ActivityIndicator color={colors.onPrimary} />
      ) : (
        <Text style={[styles.label, { color: colors.onPrimary }]}>{label}</Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: 'center',
    borderRadius: Radius.md,
    justifyContent: 'center',
    minHeight: 54,
    paddingHorizontal: Spacing.lg,
  },
  disabled: {
    opacity: 0.5,
  },
  label: {
    fontSize: 16,
    fontWeight: '800',
  },
});
