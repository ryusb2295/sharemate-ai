import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { AppButton } from '@/components/app-button';
import { AppTextField } from '@/components/app-text-field';
import { CheckRow } from '@/components/check-row';
import { EmptyState } from '@/components/empty-state';
import { ScreenContainer } from '@/components/screen-container';
import { Radius, Spacing, Typography } from '@/constants/theme';
import { useRoomTheme } from '@/hooks/use-room-theme';
import { useAuth } from '@/contexts/auth-context';

type ShoppingItem = { id: string; name: string; requestedBy: string; purchased: boolean };
const initialItems: ShoppingItem[] = [];

export default function ShoppingScreen() {
  const colors = useRoomTheme();
  const { user } = useAuth();
  const [items, setItems] = useState(initialItems);
  const [newItem, setNewItem] = useState('');
  const addItem = () => { const name = newItem.trim(); if (!name || !user) return; setItems((current) => [...current, { id: `${Date.now()}`, name, requestedBy: `${user.display_name} 요청`, purchased: false }]); setNewItem(''); };
  const toggleItem = (id: string) => setItems((current) => current.map((item) => item.id === id ? { ...item, purchased: !item.purchased } : item));
  const remaining = items.filter((item) => !item.purchased).length;

  return (
    <ScreenContainer keyboardAware subtitle="함께 필요한 물품을 한곳에서 관리하세요." title="장바구니">
      <View style={styles.section}>
        <Text style={[Typography.sectionTitle, { color: colors.textPrimary }]}>품목 추가</Text>
        <AppTextField label="공동 물품" onChangeText={setNewItem} onSubmitEditing={addItem} placeholder="예: 주방 세제" returnKeyType="done" value={newItem} />
        <AppButton disabled={!newItem.trim()} icon="add" label="목록에 추가" onPress={addItem} variant="secondary" />
      </View>

      <View style={styles.section}>
        <View style={styles.heading}><Text style={[Typography.sectionTitle, { color: colors.textPrimary }]}>공동 물품</Text><Text style={[styles.count, { color: colors.textSecondary }]}>구매 전 {remaining}개</Text></View>
        {items.length === 0 ? <EmptyState description="필요한 공동 물품을 추가해보세요." icon="shopping-cart" title="장바구니가 비어 있어요" /> : (
          <View style={[styles.list, { backgroundColor: colors.surface, borderColor: colors.border }]}>{items.map((item, index) => <View key={item.id}><CheckRow checked={item.purchased} detail={item.purchased ? `${item.requestedBy} · 구매 완료` : item.requestedBy} label={item.name} onToggle={() => toggleItem(item.id)} />{index < items.length - 1 ? <View style={[styles.divider, { backgroundColor: colors.divider }]} /> : null}</View>)}</View>
        )}
      </View>
      <Text style={[styles.helper, { color: colors.textSecondary }]}>완료한 품목도 기록을 위해 목록에 남습니다.</Text>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  section: { gap: Spacing.item }, heading: { alignItems: 'baseline', flexDirection: 'row', justifyContent: 'space-between' }, count: { fontSize: 12 },
  list: { borderRadius: Radius.card, borderWidth: 1, paddingHorizontal: Spacing.item }, divider: { height: StyleSheet.hairlineWidth, marginLeft: 37 },
  helper: { fontSize: 12, lineHeight: 18, marginTop: -12, textAlign: 'center' },
});
