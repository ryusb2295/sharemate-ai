import { useCallback, useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { AppButton } from '@/components/app-button';
import { AppTextField } from '@/components/app-text-field';
import { EmptyState } from '@/components/empty-state';
import { InlineError } from '@/components/inline-error';
import { ListRow } from '@/components/list-row';
import { LoadingOverlay } from '@/components/loading-overlay';
import { ScreenContainer } from '@/components/screen-container';
import { Spacing, Typography } from '@/constants/theme';
import { useAuth } from '@/contexts/auth-context';
import { useRoomTheme } from '@/hooks/use-room-theme';
import { apiRequest } from '@/services/api';
import type { House } from '@/types/api';

export default function HouseSelectScreen() {
  const colors = useRoomTheme();
  const { token, user, selectHouse, logout } = useAuth();
  const [houses, setHouses] = useState<House[]>([]);
  const [name, setName] = useState('');
  const [location, setLocation] = useState('');
  const [touched, setTouched] = useState(false);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [inviteCode, setInviteCode] = useState('');
  const [joining, setJoining] = useState(false);
  const [joinError, setJoinError] = useState<string | null>(null);

  const loadHouses = useCallback(async () => {
    if (!token) return;
    setLoading(true); setLoadError(null);
    try { setHouses(await apiRequest<House[]>('/houses', { token })); }
    catch (error) { setLoadError(error instanceof Error ? error.message : '하우스를 불러오지 못했습니다.'); }
    finally { setLoading(false); }
  }, [token]);

  useEffect(() => { loadHouses(); }, [loadHouses]);

  const validName = name.trim().length >= 3;
  const validLocation = location.trim().length > 0;
  const canCreate = validName && validLocation && !creating;
  const validInviteCode = /^[A-Z0-9]{6,8}$/.test(inviteCode);

  const createHouse = async () => {
    setTouched(true);
    if (!token || !canCreate) return;
    setCreating(true); setFormError(null);
    try {
      const house = await apiRequest<House>('/houses', { method: 'POST', token, body: { name: name.trim(), location: location.trim() } });
      setHouses((current) => [house, ...current]);
      setName(''); setLocation('');
      await selectHouse(house);
    } catch (error) { setFormError(error instanceof Error ? error.message : '하우스를 만들지 못했습니다.'); }
    finally { setCreating(false); }
  };

  const joinHouse = async () => {
    if (!token || !validInviteCode || joining) return;
    setJoining(true);
    setJoinError(null);
    try {
      const house = await apiRequest<House>('/houses/join', {
        method: 'POST',
        token,
        body: { invite_code: inviteCode },
      });
      setHouses((current) => [house, ...current.filter((item) => item.id !== house.id)]);
      setInviteCode('');
      await selectHouse(house);
    } catch (error) {
      setJoinError(error instanceof Error ? error.message : '하우스에 참여하지 못했습니다.');
    } finally {
      setJoining(false);
    }
  };

  return (
    <ScreenContainer
      headerAction={<AppButton fullWidth={false} label="로그아웃" onPress={logout} variant="tertiary" />}
      keyboardAware
      subtitle={`${user?.display_name ?? ''}님이 생활할 공간을 선택하세요.`}
      title="하우스 선택">
      <View style={styles.section}>
        <Text style={[Typography.sectionTitle, { color: colors.textPrimary }]}>참여 중인 하우스</Text>
        {loadError && houses.length === 0 ? (
          <View style={styles.feedback}><InlineError message={loadError} /><AppButton label="다시 시도" onPress={loadHouses} variant="secondary" /></View>
        ) : houses.length === 0 && !loading ? (
          <EmptyState description="아래에서 첫 하우스를 만들면 구성원을 초대할 수 있어요." icon="home-work" title="아직 참여 중인 하우스가 없어요" />
        ) : (
          <View style={[styles.list, { backgroundColor: colors.surface, borderColor: colors.border }]}>
            {houses.map((house, index) => (
              <View key={house.id}>
                <ListRow icon="apartment" onPress={() => selectHouse(house)} subtitle={`${house.location} · 구성원 ${house.member_count}명`} title={house.name} />
                {index < houses.length - 1 ? <View style={[styles.divider, { backgroundColor: colors.divider }]} /> : null}
              </View>
            ))}
          </View>
        )}
      </View>

      <View style={styles.section}>
        <View style={styles.sectionHeading}>
          <Text style={[Typography.sectionTitle, { color: colors.textPrimary }]}>새 하우스 만들기</Text>
          <Text style={[styles.description, { color: colors.textSecondary }]}>생성한 계정이 하우스 관리자로 등록됩니다.</Text>
        </View>
        <AppTextField error={touched && !validName ? '하우스 이름을 3자 이상 입력해주세요.' : null} label="하우스 이름" onChangeText={(value) => { setName(value); setFormError(null); }} placeholder="예: Sydney House" value={name} />
        <AppTextField error={touched && !validLocation ? '지역을 입력해주세요.' : null} label="지역" onChangeText={(value) => { setLocation(value); setFormError(null); }} onSubmitEditing={createHouse} placeholder="예: Sydney" returnKeyType="done" value={location} />
        {formError ? <InlineError message={formError} /> : null}
        <AppButton disabled={!canCreate} label="하우스 만들기" loading={creating} onPress={createHouse} />
      </View>

      <View style={styles.section}>
        <View style={styles.sectionHeading}>
          <Text style={[Typography.sectionTitle, { color: colors.textPrimary }]}>초대코드로 참여하기</Text>
          <Text style={[styles.description, { color: colors.textSecondary }]}>하우스 구성원에게 받은 6~8자리 코드를 입력하세요.</Text>
        </View>
        <AppTextField
          autoCapitalize="characters"
          autoCorrect={false}
          error={joinError}
          label="초대코드"
          maxLength={8}
          onChangeText={(value) => {
            setInviteCode(value.replace(/\s/g, '').toUpperCase());
            setJoinError(null);
          }}
          onSubmitEditing={joinHouse}
          placeholder="AB12CD34"
          returnKeyType="join"
          value={inviteCode}
        />
        <AppButton
          disabled={!validInviteCode || joining}
          label="하우스 참여"
          loading={joining}
          onPress={joinHouse}
          variant="secondary"
        />
      </View>
      <LoadingOverlay label="하우스를 불러오는 중" visible={loading} />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  section: { gap: Spacing.item },
  sectionHeading: { gap: 5 },
  description: { fontSize: 13, lineHeight: 19 },
  feedback: { gap: Spacing.item },
  list: { borderRadius: 16, borderWidth: 1, paddingHorizontal: Spacing.item },
  divider: { height: StyleSheet.hairlineWidth, marginLeft: 52 },
});
