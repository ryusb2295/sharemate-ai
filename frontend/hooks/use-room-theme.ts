import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';

export function useRoomTheme() {
  const colorScheme = useColorScheme() ?? 'light';

  return Colors[colorScheme];
}
