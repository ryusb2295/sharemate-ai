import { useRouter } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { AppButton } from '@/components/app-button';
import { ListRow } from '@/components/list-row';
import { ScreenContainer } from '@/components/screen-container';
import { Radius, Spacing, Typography } from '@/constants/theme';
import { useAuth } from '@/contexts/auth-context';
import { useRoomTheme } from '@/hooks/use-room-theme';

export default function HomeScreen() {
  const router = useRouter();
  const colors = useRoomTheme();
  const { currentHouse, user } = useAuth();
  const firstName = user?.display_name ?? '룸메이트';

  return (
    <ScreenContainer subtitle={`${firstName}님, 오늘도 편안한 하루 보내세요.`} title="홈">
      <View style={[styles.house, { backgroundColor: colors.primarySoft }]}>
        <Text style={[styles.houseLabel, { color: colors.primary }]}>현재 하우스</Text>
        <Text style={[styles.houseName, { color: colors.textPrimary }]}>{currentHouse?.name}</Text>
        <Text style={[styles.houseMeta, { color: colors.textSecondary }]}>{currentHouse?.location} · 구성원 {currentHouse?.member_count}명</Text>
      </View>

      <View style={styles.primaryAction}>
        <Text style={[Typography.sectionTitle, { color: colors.textPrimary }]}>공동 지출이 생겼나요?</Text>
        <Text style={[styles.sectionDescription, { color: colors.textSecondary }]}>영수증 사진을 선택하면 품목을 자동으로 정리해요.</Text>
        <AppButton icon="add-a-photo" label="영수증 등록" onPress={() => router.push('/settlement')} />
      </View>

      <View style={styles.section}>
        <Text style={[Typography.sectionTitle, { color: colors.textPrimary }]}>오늘의 생활</Text>
        <View style={[styles.list, { backgroundColor: colors.surface, borderColor: colors.border }]}>
          <ListRow icon="cleaning-services" onPress={() => router.push('/cleaning')} subtitle="현재 하우스의 실제 일정을 확인하세요" title="오늘의 청소" />
          <View style={[styles.divider, { backgroundColor: colors.divider }]} />
          <ListRow icon="receipt-long" onPress={() => router.push('/settlement')} subtitle="영수증과 정산 내역 확인" title="진행 중 정산" />
          <View style={[styles.divider, { backgroundColor: colors.divider }]} />
          <ListRow icon="shopping-cart" onPress={() => router.push('/shopping')} subtitle="공동 물품 목록 확인" title="공동 장바구니" />
        </View>
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  house: { borderRadius: Radius.card, padding: Spacing.item },
  houseLabel: { fontSize: 12, fontWeight: '800', marginBottom: 5 },
  houseName: { fontSize: 19, fontWeight: '800' },
  houseMeta: { fontSize: 13, marginTop: 4 },
  primaryAction: { gap: 9 },
  sectionDescription: { fontSize: 14, lineHeight: 20, marginBottom: 7 },
  section: { gap: Spacing.item },
  list: { borderRadius: Radius.card, borderWidth: 1, paddingHorizontal: Spacing.item },
  divider: { height: StyleSheet.hairlineWidth, marginLeft: 52 },
});
