import { useCallback, useEffect, useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { AppButton } from '@/components/app-button';
import { CheckRow } from '@/components/check-row';
import { EmptyState } from '@/components/empty-state';
import { InlineError } from '@/components/inline-error';
import { ListRow } from '@/components/list-row';
import { LoadingOverlay } from '@/components/loading-overlay';
import { ScreenContainer } from '@/components/screen-container';
import { StatusBadge } from '@/components/status-badge';
import { Radius, Spacing, Typography } from '@/constants/theme';
import { useAuth } from '@/contexts/auth-context';
import { useRoomTheme } from '@/hooks/use-room-theme';
import { apiRequest } from '@/services/api';
import type { Chore } from '@/types/api';

function localDateKey(date = new Date()): string {
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${date.getFullYear()}-${month}-${day}`;
}

function formatDueDate(value: string): string {
  const [year, month, day] = value.slice(0, 10).split('-');
  return year && month && day ? `${month}월 ${day}일` : value;
}

export default function CleaningScreen() {
  const colors = useRoomTheme();
  const { currentHouse, token, user } = useAuth();
  const [chores, setChores] = useState<Chore[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadChores = useCallback(async () => {
    if (!token || !currentHouse) return;
    setLoading(true);
    setError(null);
    try {
      const result = await apiRequest<Chore[]>(`/houses/${currentHouse.id}/chores`, { token });
      const validatedResult = currentHouse.member_count === 1
        ? result.filter((chore) => chore.assignee.user_id === user?.id)
        : result;
      setChores(validatedResult);
    } catch (requestError) {
      setChores([]);
      setError(requestError instanceof Error ? requestError.message : '청소 일정을 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  }, [currentHouse, token, user?.id]);

  useEffect(() => { loadChores(); }, [loadChores]);

  const toggleChore = async (chore: Chore) => {
    if (!token || !currentHouse || updatingId !== null) return;
    setUpdatingId(chore.id);
    setError(null);
    try {
      const updated = await apiRequest<Chore>(`/houses/${currentHouse.id}/chores/${chore.id}`, {
        method: 'PATCH',
        token,
        body: { status: chore.status === '완료' ? '진행 전' : '완료' },
      });
      setChores((current) => current.map((item) => item.id === updated.id ? updated : item));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '청소 상태를 변경하지 못했습니다.');
    } finally {
      setUpdatingId(null);
    }
  };

  const todayKey = localDateKey();
  const todayChores = useMemo(() => chores.filter((chore) => chore.due_date.slice(0, 10) === todayKey), [chores, todayKey]);
  const nextChores = useMemo(() => chores.filter((chore) => chore.due_date.slice(0, 10) > todayKey), [chores, todayKey]);
  const todayAssignees = [...new Set(todayChores.map((chore) => chore.assignee.display_name))];
  const completed = todayChores.filter((chore) => chore.status === '완료').length;

  return (
    <ScreenContainer subtitle={`${currentHouse?.name ?? '현재 하우스'}의 실제 청소 일정입니다.`} title="청소">
      {error ? <View style={styles.errorState}><InlineError message={error} /><AppButton label="다시 시도" onPress={loadChores} variant="secondary" /></View> : null}

      {!loading && !error && chores.length === 0 ? (
        <EmptyState description="현재 하우스에 저장된 청소 일정이 없습니다." icon="cleaning-services" title="등록된 청소 일정이 없어요" />
      ) : null}

      {!loading && !error && chores.length > 0 ? (
        <>
          {todayChores.length > 0 ? (
            <>
              <View style={[styles.assignee, { backgroundColor: colors.primarySoft }]}>
                <View style={[styles.avatar, { backgroundColor: colors.primary }]}><Text style={styles.avatarText}>{todayAssignees[0]?.slice(0, 1)}</Text></View>
                <View style={styles.copy}><Text style={[styles.label, { color: colors.primary }]}>오늘의 담당자</Text><Text style={[styles.name, { color: colors.textPrimary }]}>{todayAssignees.join(', ')}</Text><Text style={[styles.detail, { color: colors.textSecondary }]}>{currentHouse?.name} 구성원</Text></View>
                <StatusBadge label="오늘" tone="info" />
              </View>
              <View style={styles.section}>
                <View style={styles.sectionHeading}><Text style={[Typography.sectionTitle, { color: colors.textPrimary }]}>오늘의 업무</Text><Text style={[styles.count, { color: colors.textSecondary }]}>{todayChores.length}개 중 {completed}개 완료</Text></View>
                <View style={[styles.list, { backgroundColor: colors.surface, borderColor: colors.border }]}>{todayChores.map((chore, index) => <View key={chore.id}><CheckRow checked={chore.status === '완료'} detail={`${chore.assignee.display_name} · ${formatDueDate(chore.due_date)}`} disabled={updatingId !== null} label={chore.title} onToggle={() => toggleChore(chore)} />{index < todayChores.length - 1 ? <View style={[styles.divider, { backgroundColor: colors.divider }]} /> : null}</View>)}</View>
              </View>
            </>
          ) : <EmptyState description="현재 하우스에 오늘로 등록된 청소 업무가 없습니다." icon="event-available" title="오늘 청소 일정이 없어요" />}

          {nextChores.length > 0 ? <View style={styles.section}><Text style={[Typography.sectionTitle, { color: colors.textPrimary }]}>다음 일정</Text><View style={[styles.list, { backgroundColor: colors.surface, borderColor: colors.border }]}>{nextChores.map((chore, index) => <View key={chore.id}><ListRow icon="event" subtitle={`${formatDueDate(chore.due_date)} · ${chore.status}`} title={`${chore.title} · ${chore.assignee.display_name}`} />{index < nextChores.length - 1 ? <View style={[styles.divider, { backgroundColor: colors.divider }]} /> : null}</View>)}</View></View> : null}
        </>
      ) : null}
      <LoadingOverlay label="청소 일정을 불러오는 중" visible={loading} />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  errorState: { gap: Spacing.item }, assignee: { alignItems: 'center', borderRadius: Radius.card, flexDirection: 'row', gap: Spacing.md, padding: Spacing.item },
  avatar: { alignItems: 'center', borderRadius: Radius.pill, height: 48, justifyContent: 'center', width: 48 }, avatarText: { color: '#FFFFFF', fontSize: 17, fontWeight: '800' },
  copy: { flex: 1, gap: 2 }, label: { fontSize: 11, fontWeight: '800' }, name: { fontSize: 18, fontWeight: '800' }, detail: { fontSize: 12 },
  section: { gap: Spacing.item }, sectionHeading: { alignItems: 'baseline', flexDirection: 'row', justifyContent: 'space-between' }, count: { fontSize: 12 },
  list: { borderRadius: Radius.card, borderWidth: 1, paddingHorizontal: Spacing.item }, divider: { height: StyleSheet.hairlineWidth, marginLeft: 37 },
});
