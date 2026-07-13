import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { useState } from 'react';
import { Pressable, StyleSheet } from 'react-native';

import { AppTextField } from '@/components/app-text-field';
import { useRoomTheme } from '@/hooks/use-room-theme';
import type { TextInputProps } from 'react-native';

type PasswordFieldProps = Omit<TextInputProps, 'secureTextEntry'> & { label: string; error?: string | null; hint?: string };

export function PasswordField(props: PasswordFieldProps) {
  const colors = useRoomTheme();
  const [visible, setVisible] = useState(false);
  return (
    <AppTextField
      {...props}
      rightAccessory={
        <Pressable
          accessibilityLabel={visible ? '비밀번호 숨기기' : '비밀번호 표시'}
          accessibilityRole="button"
          hitSlop={8}
          onPress={() => setVisible((current) => !current)}
          style={styles.toggle}>
          <MaterialIcons color={colors.textSecondary} name={visible ? 'visibility-off' : 'visibility'} size={22} />
        </Pressable>
      }
      secureTextEntry={!visible}
    />
  );
}

const styles = StyleSheet.create({ toggle: { alignItems: 'center', height: 48, justifyContent: 'center', width: 48 } });
