import { useState } from 'react';
import { StyleSheet, Switch, Text, View } from 'react-native';

import { InlineError } from '@/components/inline-error';
import { ListRow } from '@/components/list-row';
import { ScreenContainer } from '@/components/screen-container';
import { Radius, Spacing } from '@/constants/theme';
import { useAuth } from '@/contexts/auth-context';
import { useRoomTheme } from '@/hooks/use-room-theme';

export default function SettingsScreen() {
  const colors = useRoomTheme();
  const { currentHouse, user, clearHouse, logout } = useAuth();
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);

  const section = (title: string, children: React.ReactNode) => (
    <View style={styles.section}><Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>{title}</Text><View style={[styles.group, { backgroundColor: colors.surface, borderColor: colors.border }]}>{children}</View></View>
  );
  const divider = <View style={[styles.divider, { backgroundColor: colors.divider }]} />;

  return (
    <ScreenContainer subtitle="하우스와 계정 환경을 관리하세요." title="설정">
      {section('하우스', <><ListRow icon="apartment" subtitle={`${currentHouse?.location} · 구성원 ${currentHouse?.member_count}명`} title={currentHouse?.name ?? '현재 하우스'} />{divider}<ListRow icon="group" onPress={() => setNotice('구성원 관리 기능은 준비 중입니다.')} subtitle="함께 생활하는 멤버 확인" title="구성원" />{divider}<ListRow icon="swap-horiz" onPress={clearHouse} subtitle="다른 하우스를 선택합니다" title="하우스 변경" /></>)}

      {section('앱 설정', <><ListRow icon="language" onPress={() => setNotice('언어 설정은 준비 중입니다.')} subtitle="한국어" title="언어" />{divider}<ListRow icon="notifications-none" subtitle="현재 기기에만 적용됩니다" title="알림" trailing={<Switch accessibilityLabel="알림 사용" ios_backgroundColor={colors.disabled} onValueChange={setNotificationsEnabled} trackColor={{ false: colors.disabled, true: colors.primary }} value={notificationsEnabled} />} /></>)}

      {section('계정', <><ListRow icon="person-outline" subtitle={user?.email} title={user?.display_name ?? '내 계정'} />{divider}<ListRow icon="logout" onPress={logout} title="로그아웃" />{divider}<ListRow destructive icon="delete-outline" onPress={() => setNotice('계정 삭제는 아직 지원되지 않습니다.')} title="계정 삭제" /></>)}
      {notice ? <InlineError message={notice} /> : null}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  section: { gap: Spacing.compact },
  sectionTitle: { fontSize: 12, fontWeight: '700', paddingHorizontal: 4, textTransform: 'uppercase' },
  group: { borderRadius: Radius.card, borderWidth: 1, paddingHorizontal: Spacing.item },
  divider: { height: StyleSheet.hairlineWidth, marginLeft: 52 },
});
