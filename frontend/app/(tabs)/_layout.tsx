import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { Tabs } from 'expo-router';

import { HapticTab } from '@/components/haptic-tab';
import { Colors } from '@/constants/theme';

export default function TabLayout() {
  const colors = Colors.light;

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.tabIconSelected,
        tabBarInactiveTintColor: colors.tabIconDefault,
        tabBarButton: HapticTab,
        tabBarHideOnKeyboard: true,
        tabBarItemStyle: { paddingVertical: 3 },
        tabBarLabelStyle: { fontSize: 11, fontWeight: '600' },
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.divider,
          borderTopWidth: 1,
          height: 82,
          paddingBottom: 9,
          paddingTop: 7,
        },
      }}>
      <Tabs.Screen
        name="index"
        options={{
          title: '홈',
          tabBarIcon: ({ color, size }) => <MaterialIcons color={color} name="home" size={size} />,
        }}
      />
      <Tabs.Screen
        name="settlement"
        options={{
          title: '정산',
          tabBarIcon: ({ color, size }) => (
            <MaterialIcons color={color} name="receipt-long" size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="cleaning"
        options={{
          title: '청소',
          tabBarIcon: ({ color, size }) => (
            <MaterialIcons color={color} name="cleaning-services" size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="shopping"
        options={{
          title: '장바구니',
          tabBarIcon: ({ color, size }) => (
            <MaterialIcons color={color} name="shopping-cart" size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: '설정',
          tabBarIcon: ({ color, size }) => (
            <MaterialIcons color={color} name="settings" size={size} />
          ),
        }}
      />
    </Tabs>
  );
}
