import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { useEffect, useState } from 'react';
import {
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { AppButton } from '@/components/app-button';
import { AppTextField } from '@/components/app-text-field';
import { InlineError } from '@/components/inline-error';
import { Radius, Spacing, Typography } from '@/constants/theme';
import { useRoomTheme } from '@/hooks/use-room-theme';
import type { HouseMember } from '@/types/api';

type ChoreDraft = {
  title: string;
  description: string;
  assigneeUserId: number;
  scheduledDate: string;
};

type Props = {
  visible: boolean;
  members: HouseMember[];
  initialAssigneeUserId?: number;
  loading: boolean;
  error?: string | null;
  onClose: () => void;
  onSubmit: (draft: ChoreDraft) => void;
};

function dateKey(date = new Date()): string {
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${date.getFullYear()}-${month}-${day}`;
}

function isValidDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00`);
  return !Number.isNaN(parsed.getTime()) && dateKey(parsed) === value;
}

export function ChoreFormModal({
  visible,
  members,
  initialAssigneeUserId,
  loading,
  error,
  onClose,
  onSubmit,
}: Props) {
  const colors = useRoomTheme();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [assigneeUserId, setAssigneeUserId] = useState<number | null>(null);
  const [scheduledDate, setScheduledDate] = useState(dateKey());
  const [dateTouched, setDateTouched] = useState(false);

  useEffect(() => {
    if (!visible) return;
    setTitle('');
    setDescription('');
    setAssigneeUserId(
      initialAssigneeUserId && members.some((member) => member.user_id === initialAssigneeUserId)
        ? initialAssigneeUserId
        : members[0]?.user_id ?? null
    );
    setScheduledDate(dateKey());
    setDateTouched(false);
  }, [initialAssigneeUserId, members, visible]);

  const validDate = isValidDate(scheduledDate);
  const canSubmit = title.trim().length > 0 && assigneeUserId !== null && validDate && !loading;

  const moveDate = (days: number) => {
    const base = isValidDate(scheduledDate)
      ? new Date(`${scheduledDate}T00:00:00`)
      : new Date();
    base.setDate(base.getDate() + days);
    setScheduledDate(dateKey(base));
    setDateTouched(true);
  };

  return (
    <Modal animationType="slide" onRequestClose={onClose} presentationStyle="pageSheet" visible={visible}>
      <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.background }]}>
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.flex}>
          <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
            <View style={styles.header}>
              <View style={styles.headerCopy}>
                <Text style={[Typography.screenTitle, { color: colors.textPrimary }]}>청소 일정 추가</Text>
                <Text style={[styles.subtitle, { color: colors.textSecondary }]}>현재 하우스에 새 담당 일정을 등록합니다.</Text>
              </View>
              <Pressable accessibilityLabel="닫기" accessibilityRole="button" disabled={loading} onPress={onClose} style={styles.close}>
                <MaterialIcons color={colors.textSecondary} name="close" size={25} />
              </Pressable>
            </View>

            <View style={styles.form}>
              <AppTextField label="청소 항목명" maxLength={100} onChangeText={setTitle} placeholder="예: 욕실 청소" value={title} />
              <AppTextField label="설명 또는 메모" maxLength={500} multiline onChangeText={setDescription} placeholder="청소 범위나 주의사항을 입력하세요" style={styles.memoInput} textAlignVertical="top" value={description} />

              <View style={styles.fieldGroup}>
                <Text style={[styles.label, { color: colors.textPrimary }]}>담당자</Text>
                {members.map((member) => {
                  const selected = member.user_id === assigneeUserId;
                  return (
                    <Pressable
                      key={member.id}
                      accessibilityRole="radio"
                      accessibilityState={{ selected }}
                      onPress={() => setAssigneeUserId(member.user_id)}
                      style={({ pressed }) => [
                        styles.memberRow,
                        { backgroundColor: selected ? colors.primarySoft : colors.surface, borderColor: selected ? colors.primary : colors.border },
                        pressed && styles.pressed,
                      ]}>
                      <MaterialIcons color={selected ? colors.primary : colors.placeholder} name={selected ? 'radio-button-checked' : 'radio-button-unchecked'} size={22} />
                      <View style={styles.memberCopy}>
                        <Text style={[styles.memberName, { color: colors.textPrimary }]}>{member.display_name}</Text>
                        <Text style={[styles.memberRole, { color: colors.textSecondary }]}>{member.role === 'owner' ? '관리자' : '멤버'}</Text>
                      </View>
                    </Pressable>
                  );
                })}
                {members.length === 0 ? <InlineError message="선택할 수 있는 하우스 멤버가 없습니다." /> : null}
              </View>

              <View style={styles.fieldGroup}>
                <AppTextField
                  error={dateTouched && !validDate ? 'YYYY-MM-DD 형식의 실제 날짜를 입력해주세요.' : null}
                  keyboardType="numbers-and-punctuation"
                  label="예정일"
                  maxLength={10}
                  onBlur={() => setDateTouched(true)}
                  onChangeText={setScheduledDate}
                  placeholder="YYYY-MM-DD"
                  value={scheduledDate}
                />
                <View style={styles.dateActions}>
                  <AppButton fullWidth={false} label="이전 날" onPress={() => moveDate(-1)} variant="tertiary" />
                  <AppButton fullWidth={false} label="오늘" onPress={() => setScheduledDate(dateKey())} variant="tertiary" />
                  <AppButton fullWidth={false} label="다음 날" onPress={() => moveDate(1)} variant="tertiary" />
                </View>
              </View>
              {error ? <InlineError message={error} /> : null}
              <AppButton
                disabled={!canSubmit}
                label="일정 등록"
                loading={loading}
                onPress={() => assigneeUserId !== null && onSubmit({ title: title.trim(), description: description.trim(), assigneeUserId, scheduledDate })}
              />
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1 }, flex: { flex: 1 }, content: { padding: Spacing.screenHorizontal, paddingBottom: 40 },
  header: { alignItems: 'flex-start', flexDirection: 'row', gap: Spacing.item, justifyContent: 'space-between' }, headerCopy: { flex: 1, gap: Spacing.compact },
  subtitle: { fontSize: 14, lineHeight: 20 }, close: { alignItems: 'center', height: 44, justifyContent: 'center', width: 44 },
  form: { gap: Spacing.item, marginTop: Spacing.section }, memoInput: { minHeight: 92, paddingTop: 14 }, fieldGroup: { gap: Spacing.compact }, label: { fontSize: 14, fontWeight: '600' },
  memberRow: { alignItems: 'center', borderRadius: Radius.input, borderWidth: 1, flexDirection: 'row', gap: Spacing.md, minHeight: 58, paddingHorizontal: Spacing.item },
  memberCopy: { flex: 1, gap: 2 }, memberName: { fontSize: 15, fontWeight: '700' }, memberRole: { fontSize: 12 }, pressed: { opacity: 0.75 },
  dateActions: { flexDirection: 'row', justifyContent: 'space-between' },
});
