import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { AppTextField } from '@/components/app-text-field';
import { StatusBadge } from '@/components/status-badge';
import { Radius, Spacing } from '@/constants/theme';
import { useRoomTheme } from '@/hooks/use-room-theme';
import type { ReceiptAnalysis, ReceiptItem } from '@/types/api';

type Props = { analysis: ReceiptAnalysis; onChange: (analysis: ReceiptAnalysis) => void };
function parseNumber(value: string): number { const parsed = Number(value.replace(',', '.')); return Number.isFinite(parsed) ? parsed : 0; }

export function ReceiptAnalysisEditor({ analysis, onChange }: Props) {
  const colors = useRoomTheme();
  const [draftItems, setDraftItems] = useState(() => analysis.items.map((item) => ({ quantity: String(item.quantity), price: String(item.price) })));
  const editedTotal = analysis.items.reduce((sum, item) => sum + item.price, 0);
  const updateItem = (index: number, patch: Partial<ReceiptItem>) => onChange({ ...analysis, items: analysis.items.map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } : item) });
  const updateNumber = (index: number, field: 'quantity' | 'price', value: string) => {
    setDraftItems((current) => current.map((draft, itemIndex) => itemIndex === index ? { ...draft, [field]: value } : draft));
    updateItem(index, { [field]: parseNumber(value) });
  };

  return (
    <View style={styles.container}>
      {analysis.warning ? <View style={[styles.warning, { backgroundColor: colors.warningSoft }]}><MaterialIcons color={colors.warning} name="info-outline" size={19} /><Text style={[styles.warningText, { color: colors.warning }]}>{analysis.warning}</Text></View> : null}
      <View style={[styles.summary, { backgroundColor: colors.surface, borderColor: colors.border }]}>
        <View style={styles.modeRow}><Text style={[styles.summaryLabel, { color: colors.textSecondary }]}>분석 정보</Text><StatusBadge label={analysis.analysis_mode === 'openai' ? 'AI 분석' : 'Mock 분석'} tone={analysis.analysis_mode === 'openai' ? 'completed' : 'pending'} /></View>
        <AppTextField label="매장명" onChangeText={(storeName) => onChange({ ...analysis, store_name: storeName })} value={analysis.store_name} />
        <View style={[styles.divider, { backgroundColor: colors.divider }]} />
        <View style={styles.totalRow}><View><Text style={[styles.summaryLabel, { color: colors.textSecondary }]}>영수증 총액</Text><Text style={[styles.total, { color: colors.textPrimary }]}>${analysis.total.toFixed(2)}</Text></View><View style={styles.alignRight}><Text style={[styles.summaryLabel, { color: colors.textSecondary }]}>수정 품목 합계</Text><Text style={[styles.editedTotal, { color: colors.primary }]}>${editedTotal.toFixed(2)}</Text></View></View>
      </View>

      <View style={styles.items}>{analysis.items.map((item, index) => (
        <View key={`${index}-${item.name}`} style={[styles.item, { backgroundColor: colors.surface, borderColor: colors.border }]}>
          <Text style={[styles.itemTitle, { color: colors.textPrimary }]}>품목 {index + 1}</Text>
          <AppTextField label="품목명" onChangeText={(name) => updateItem(index, { name })} value={item.name} />
          <View style={styles.numberRow}>
            <View style={styles.quantity}><AppTextField keyboardType="decimal-pad" label="수량" onChangeText={(value) => updateNumber(index, 'quantity', value)} value={draftItems[index]?.quantity ?? String(item.quantity)} /></View>
            <View style={styles.price}><AppTextField keyboardType="numbers-and-punctuation" label="금액" onChangeText={(value) => updateNumber(index, 'price', value)} value={draftItems[index]?.price ?? String(item.price)} /></View>
          </View>
        </View>
      ))}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: Spacing.item }, warning: { alignItems: 'flex-start', borderRadius: Radius.input, flexDirection: 'row', gap: Spacing.compact, padding: Spacing.md }, warningText: { flex: 1, fontSize: 12, lineHeight: 18 },
  summary: { borderRadius: Radius.card, borderWidth: 1, gap: Spacing.item, padding: Spacing.item }, modeRow: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' }, summaryLabel: { fontSize: 11, fontWeight: '700' }, divider: { height: StyleSheet.hairlineWidth },
  totalRow: { alignItems: 'flex-end', flexDirection: 'row', justifyContent: 'space-between' }, total: { fontSize: 21, fontWeight: '800', marginTop: 4 }, alignRight: { alignItems: 'flex-end' }, editedTotal: { fontSize: 17, fontWeight: '800', marginTop: 4 },
  items: { gap: Spacing.item }, item: { borderRadius: Radius.card, borderWidth: 1, gap: Spacing.item, padding: Spacing.item }, itemTitle: { fontSize: 14, fontWeight: '800' }, numberRow: { flexDirection: 'row', gap: Spacing.md }, quantity: { width: 92 }, price: { flex: 1 },
});
