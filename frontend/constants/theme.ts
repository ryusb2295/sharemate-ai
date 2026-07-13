import { Platform } from 'react-native';

export const AppColors = {
  background: '#F7F9FC',
  surface: '#FFFFFF',
  primary: '#246BFD',
  primaryPressed: '#1854D8',
  primarySoft: '#EAF1FF',
  textPrimary: '#111827',
  textSecondary: '#6B7280',
  placeholder: '#9CA3AF',
  border: '#E5E7EB',
  divider: '#EEF0F3',
  success: '#16A36A',
  warning: '#E58A17',
  danger: '#DC4C4C',
  disabled: '#CBD2DC',
} as const;

const roomColors = {
  ...AppColors,
  text: AppColors.textPrimary,
  secondaryText: AppColors.textSecondary,
  surfaceMuted: AppColors.background,
  onPrimary: AppColors.surface,
  tint: AppColors.primary,
  tintSoft: AppColors.primarySoft,
  icon: AppColors.textSecondary,
  tabIconDefault: AppColors.placeholder,
  tabIconSelected: AppColors.primary,
  successSoft: '#E9F7F1',
  warningSoft: '#FFF5E8',
  dangerSoft: '#FFF0F0',
} as const;

// RoomSync currently uses a light, white-led interface on every supported device.
export const Colors = { light: roomColors, dark: roomColors } as const;

export const Spacing = {
  screenHorizontal: 24,
  section: 28,
  item: 16,
  compact: 8,
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
} as const;

export const Radius = {
  input: 12,
  button: 12,
  card: 16,
  sheet: 22,
  sm: 10,
  md: 12,
  lg: 16,
  pill: 999,
} as const;

export const Layout = {
  screenPadding: Spacing.screenHorizontal,
  sectionGap: Spacing.section,
  cardPadding: Spacing.item,
  controlHeight: 52,
} as const;

export const Typography = {
  screenTitle: { fontSize: 30, fontWeight: '800' as const, letterSpacing: -0.8 },
  sectionTitle: { fontSize: 18, fontWeight: '700' as const, letterSpacing: -0.2 },
  body: { fontSize: 15, lineHeight: 22 },
  caption: { fontSize: 13, lineHeight: 18 },
} as const;

export const Fonts = Platform.select({
  ios: { sans: 'system-ui', serif: 'ui-serif', rounded: 'ui-rounded', mono: 'ui-monospace' },
  default: { sans: 'normal', serif: 'serif', rounded: 'normal', mono: 'monospace' },
  web: {
    sans: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    serif: "Georgia, 'Times New Roman', serif",
    rounded: "'SF Pro Rounded', 'Hiragino Maru Gothic ProN', Meiryo, sans-serif",
    mono: "SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace",
  },
});
