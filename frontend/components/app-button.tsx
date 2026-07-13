import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import type { ComponentProps } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text } from 'react-native';

import { Layout, Radius, Spacing } from '@/constants/theme';
import { useRoomTheme } from '@/hooks/use-room-theme';

type IconName = ComponentProps<typeof MaterialIcons>['name'];
type ButtonVariant = 'primary' | 'secondary' | 'tertiary' | 'danger';

type AppButtonProps = {
  label: string;
  onPress: () => void;
  variant?: ButtonVariant;
  icon?: IconName;
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
};

export function AppButton({
  label,
  onPress,
  variant = 'primary',
  icon,
  loading = false,
  disabled = false,
  fullWidth = true,
}: AppButtonProps) {
  const colors = useRoomTheme();
  const unavailable = disabled || loading;
  const foreground = variant === 'primary' ? colors.onPrimary : variant === 'danger' ? colors.danger : colors.primary;

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: unavailable, busy: loading }}
      disabled={unavailable}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        fullWidth && styles.fullWidth,
        variant === 'primary' && { backgroundColor: pressed ? colors.primaryPressed : colors.primary, borderColor: colors.primary },
        variant === 'secondary' && { backgroundColor: pressed ? colors.primarySoft : colors.surface, borderColor: colors.border },
        variant === 'tertiary' && { backgroundColor: pressed ? colors.primarySoft : 'transparent', borderColor: 'transparent' },
        variant === 'danger' && { backgroundColor: pressed ? colors.dangerSoft : colors.surface, borderColor: colors.border },
        unavailable && { backgroundColor: variant === 'primary' ? colors.disabled : colors.surface, borderColor: colors.border, opacity: 0.78 },
      ]}>
      {loading ? (
        <ActivityIndicator color={variant === 'primary' ? colors.onPrimary : foreground} />
      ) : (
        <>
          {icon ? <MaterialIcons color={unavailable ? colors.textSecondary : foreground} name={icon} size={20} /> : null}
          <Text style={[styles.label, { color: unavailable ? colors.textSecondary : foreground }]}>{label}</Text>
        </>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: 'center',
    alignSelf: 'flex-start',
    borderRadius: Radius.button,
    borderWidth: 1,
    flexDirection: 'row',
    gap: Spacing.compact,
    justifyContent: 'center',
    minHeight: Layout.controlHeight,
    paddingHorizontal: Spacing.item,
  },
  fullWidth: { alignSelf: 'stretch' },
  label: { fontSize: 16, fontWeight: '700' },
});
