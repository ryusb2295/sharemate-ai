import { StyleSheet, Text, TextInput, type TextInputProps, View } from 'react-native';

import { Radius, Spacing } from '@/constants/theme';
import { useRoomTheme } from '@/hooks/use-room-theme';

type FormFieldProps = TextInputProps & {
  label: string;
};

export function FormField({ label, style, ...props }: FormFieldProps) {
  const colors = useRoomTheme();

  return (
    <View style={styles.container}>
      <Text style={[styles.label, { color: colors.text }]}>{label}</Text>
      <TextInput
        autoCapitalize="none"
        placeholderTextColor={colors.secondaryText}
        style={[
          styles.input,
          { backgroundColor: colors.surface, borderColor: colors.border, color: colors.text },
          style,
        ]}
        {...props}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: Spacing.sm,
  },
  label: {
    fontSize: 14,
    fontWeight: '700',
  },
  input: {
    borderRadius: Radius.md,
    borderWidth: 1,
    fontSize: 16,
    minHeight: 52,
    paddingHorizontal: Spacing.lg,
  },
});
