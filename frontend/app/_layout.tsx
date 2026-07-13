import { DefaultTheme, ThemeProvider } from '@react-navigation/native';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import 'react-native-reanimated';

import { Colors } from '@/constants/theme';
import { AuthProvider, useAuth } from '@/contexts/auth-context';

function RootNavigator() {
  const baseTheme = DefaultTheme;
  const appColors = Colors.light;
  const { isLoading, token, currentHouse } = useAuth();

  const navigationTheme = {
    ...baseTheme,
    colors: {
      ...baseTheme.colors,
      background: appColors.background,
      card: appColors.surface,
      primary: appColors.primary,
      text: appColors.text,
      border: appColors.border,
    },
  };

  return (
    <ThemeProvider value={navigationTheme}>
      {isLoading ? (
        <View style={[styles.loading, { backgroundColor: appColors.background }]}>
          <ActivityIndicator color={appColors.primary} size="large" />
        </View>
      ) : (
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Protected guard={!token}>
            <Stack.Screen name="(auth)" />
          </Stack.Protected>
          <Stack.Protected guard={Boolean(token) && !currentHouse}>
            <Stack.Screen name="house-select" />
          </Stack.Protected>
          <Stack.Protected guard={Boolean(token) && Boolean(currentHouse)}>
            <Stack.Screen name="(tabs)" />
          </Stack.Protected>
        </Stack>
      )}
      <StatusBar style="dark" />
    </ThemeProvider>
  );
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <RootNavigator />
    </AuthProvider>
  );
}

const styles = StyleSheet.create({
  loading: {
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
  },
});
