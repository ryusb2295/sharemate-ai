import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import type { ComponentProps } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Radius, Spacing } from '@/constants/theme';
import { useRoomTheme } from '@/hooks/use-room-theme';

type MaterialIconName = ComponentProps<typeof MaterialIcons>['name'];

type ActionButtonProps = {
  title: string;
  description: string;
  icon: MaterialIconName;
  primary?: boolean;
  onPress: () => void;
};

export function ActionButton({
  title,
  description,
  icon,
  primary = false,
  onPress,
}: ActionButtonProps) {
  const colors = useRoomTheme();
  const backgroundColor = primary ? colors.primary : colors.surface;
  const foregroundColor = primary ? colors.onPrimary : colors.text;
  const detailColor = primary ? colors.onPrimary : colors.secondaryText;

  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        {
          backgroundColor: pressed
            ? primary
              ? colors.primaryPressed
              : colors.surfaceMuted
            : backgroundColor,
          borderColor: primary ? colors.primary : colors.border,
        },
      ]}>
      <View
        style={[
          styles.iconBox,
          { backgroundColor: primary ? 'rgba(255,255,255,0.18)' : colors.tintSoft },
        ]}>
        <MaterialIcons color={primary ? colors.onPrimary : colors.primary} name={icon} size={25} />
      </View>
      <View style={styles.copy}>
        <Text style={[styles.title, { color: foregroundColor }]}>{title}</Text>
        <Text style={[styles.description, { color: detailColor }]}>{description}</Text>
      </View>
      <MaterialIcons color={detailColor} name="chevron-right" size={25} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: 'center',
    borderRadius: Radius.lg,
    borderWidth: 1,
    flexDirection: 'row',
    gap: Spacing.md,
    minHeight: 80,
    padding: Spacing.lg,
  },
  iconBox: {
    alignItems: 'center',
    borderRadius: Radius.md,
    height: 46,
    justifyContent: 'center',
    width: 46,
  },
  copy: {
    flex: 1,
    gap: Spacing.xs,
  },
  title: {
    fontSize: 17,
    fontWeight: '700',
  },
  description: {
    fontSize: 13,
    lineHeight: 18,
    opacity: 0.9,
  },
});
