import type { ReactNode } from 'react';
import { forwardRef } from 'react';
import { StyleSheet, Text, TextInput, View, type TextInputProps } from 'react-native';

import { InlineError } from '@/components/inline-error';
import { Layout, Radius, Spacing } from '@/constants/theme';
import { useRoomTheme } from '@/hooks/use-room-theme';

type AppTextFieldProps = TextInputProps & {
  label: string;
  error?: string | null;
  hint?: string;
  rightAccessory?: ReactNode;
};

export const AppTextField = forwardRef<TextInput, AppTextFieldProps>(function AppTextField(
  { label, error, hint, rightAccessory, style, ...props }, ref
) {
  const colors = useRoomTheme();
  return (
    <View style={styles.field}>
      <Text style={[styles.label, { color: colors.textPrimary }]}>{label}</Text>
      <View style={[styles.inputShell, { backgroundColor: colors.surface, borderColor: error ? colors.danger : colors.border }]}>
        <TextInput
          ref={ref}
          placeholderTextColor={colors.placeholder}
          selectionColor={colors.primary}
          style={[styles.input, { color: colors.textPrimary }, style]}
          {...props}
        />
        {rightAccessory}
      </View>
      {error ? <InlineError message={error} /> : hint ? <Text style={[styles.hint, { color: colors.textSecondary }]}>{hint}</Text> : null}
    </View>
  );
});

const styles = StyleSheet.create({
  field: { gap: 7 },
  label: { fontSize: 14, fontWeight: '600' },
  inputShell: { alignItems: 'center', borderRadius: Radius.input, borderWidth: 1, flexDirection: 'row', minHeight: Layout.controlHeight },
  input: { flex: 1, fontSize: 16, minHeight: Layout.controlHeight, paddingHorizontal: Spacing.item, paddingVertical: 0 },
  hint: { fontSize: 12, lineHeight: 17 },
});
