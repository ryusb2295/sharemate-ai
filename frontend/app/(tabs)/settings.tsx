import * as Clipboard from 'expo-clipboard';
import type { ReactNode } from 'react';
import { useCallback, useEffect, useState } from 'react';
import { StyleSheet, Switch, Text, View } from 'react-native';

import { AppButton } from '@/components/app-button';
import { EmptyState } from '@/components/empty-state';
import { InlineError } from '@/components/inline-error';
import { ListRow } from '@/components/list-row';
import { ScreenContainer } from '@/components/screen-container';
import { StatusBadge } from '@/components/status-badge';
import { Radius, Spacing } from '@/constants/theme';
import { useAuth } from '@/contexts/auth-context';
import { useRoomTheme } from '@/hooks/use-room-theme';
import { apiRequest } from '@/services/api';
import type { House } from '@/types/api';

export default function SettingsScreen() {
  const colors = useRoomTheme();
  const {
    currentHouse,
    user,
    token,
    houseMembers,
    membersLoading,
    membersError,
    refreshHouseMembers,
    clearHouse,
    logout,
  } = useAuth();
  const [houseDetails, setHouseDetails] = useState(currentHouse);
  const [houseError, setHouseError] = useState<string | null>(null);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);

  const loadHouseDetails = useCallback(async () => {
    if (!token || !currentHouse) return;
    setHouseError(null);
    try {
      setHouseDetails(await apiRequest<House>(`/houses/${currentHouse.id}`, { token }));
    } catch (error) {
      setHouseError(error instanceof Error ? error.message : '하우스 정보를 불러오지 못했습니다.');
    }
  }, [currentHouse, token]);

  useEffect(() => { loadHouseDetails(); }, [loadHouseDetails]);

  const copyInviteCode = async () => {
    if (!houseDetails?.invite_code) return;
    await Clipboard.setStringAsync(houseDetails.invite_code);
    setCopySuccess(true);
  };

  const section = (title: string, children: ReactNode) => (
    <View style={styles.section}>
      <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>{title}</Text>
      <View style={[styles.group, { backgroundColor: colors.surface, borderColor: colors.border }]}>{children}</View>
    </View>
  );
  const divider = <View style={[styles.divider, { backgroundColor: colors.divider }]} />;

  return (
    <ScreenContainer subtitle="하우스와 계정 환경을 관리하세요." title="설정">
      {section('하우스 정보', <>
        <ListRow icon="apartment" subtitle={`${houseDetails?.location ?? ''} · 구성원 ${houseDetails?.member_count ?? houseMembers.length}명`} title={houseDetails?.name ?? '현재 하우스'} />
        {divider}
        <View style={styles.inviteRow}>
          <View style={styles.inviteCopy}>
            <Text style={[styles.inviteLabel, { color: colors.textSecondary }]}>초대코드</Text>
            <Text selectable style={[styles.inviteCode, { color: colors.textPrimary }]}>{houseDetails?.invite_code}</Text>
            {copySuccess ? <Text style={[styles.successText, { color: colors.success }]}>복사되었습니다.</Text> : null}
          </View>
          <AppButton fullWidth={false} icon="content-copy" label="복사" onPress={copyInviteCode} variant="secondary" />
        </View>
        {divider}
        <ListRow icon="swap-horiz" onPress={clearHouse} subtitle="다른 하우스를 선택합니다" title="하우스 변경" />
      </>)}
      {houseError ? <View style={styles.feedback}><InlineError message={houseError} /><AppButton label="하우스 정보 다시 불러오기" onPress={loadHouseDetails} variant="secondary" /></View> : null}

      <View style={styles.section}>
        <View style={styles.memberHeader}>
          <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>구성원</Text>
          <AppButton fullWidth={false} label="새로고침" onPress={refreshHouseMembers} variant="tertiary" />
        </View>
        {membersError ? <View style={styles.feedback}><InlineError message={membersError} /><AppButton label="다시 시도" onPress={refreshHouseMembers} variant="secondary" /></View> : membersLoading ? <Text style={[styles.loadingText, { color: colors.textSecondary }]}>멤버를 불러오는 중...</Text> : houseMembers.length === 0 ? <EmptyState description="현재 확인할 수 있는 멤버가 없습니다." icon="group" title="구성원이 없어요" /> : (
          <View style={[styles.group, { backgroundColor: colors.surface, borderColor: colors.border }]}>{houseMembers.map((member, index) => <View key={member.id}><ListRow icon="person-outline" subtitle={member.email} title={member.display_name} trailing={<StatusBadge label={member.role === 'owner' ? '관리자' : '멤버'} tone={member.role === 'owner' ? 'info' : 'completed'} />} />{index < houseMembers.length - 1 ? divider : null}</View>)}</View>
        )}
      </View>

      {section('앱 설정', <><ListRow icon="language" onPress={() => setNotice('언어 설정은 준비 중입니다.')} subtitle="한국어" title="언어" />{divider}<ListRow icon="notifications-none" subtitle="현재 기기에만 적용됩니다" title="알림" trailing={<Switch accessibilityLabel="알림 사용" ios_backgroundColor={colors.disabled} onValueChange={setNotificationsEnabled} trackColor={{ false: colors.disabled, true: colors.primary }} value={notificationsEnabled} />} /></>)}
      {section('계정', <><ListRow icon="person-outline" subtitle={user?.email} title={user?.display_name ?? '내 계정'} />{divider}<ListRow icon="logout" onPress={logout} title="로그아웃" />{divider}<ListRow destructive icon="delete-outline" onPress={() => setNotice('계정 삭제는 아직 지원되지 않습니다.')} title="계정 삭제" /></>)}
      {notice ? <InlineError message={notice} /> : null}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  section: { gap: Spacing.compact }, sectionTitle: { fontSize: 12, fontWeight: '700', paddingHorizontal: 4, textTransform: 'uppercase' },
  group: { borderRadius: Radius.card, borderWidth: 1, paddingHorizontal: Spacing.item }, divider: { height: StyleSheet.hairlineWidth, marginLeft: 52 },
  inviteRow: { alignItems: 'center', flexDirection: 'row', gap: Spacing.item, minHeight: 84, paddingVertical: Spacing.compact }, inviteCopy: { flex: 1, gap: 3 },
  inviteLabel: { fontSize: 12, fontWeight: '600' }, inviteCode: { fontSize: 20, fontWeight: '800', letterSpacing: 1.5 }, successText: { fontSize: 11, fontWeight: '700' },
  memberHeader: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' }, feedback: { gap: Spacing.item }, loadingText: { fontSize: 13, paddingVertical: Spacing.item, textAlign: 'center' },
});
