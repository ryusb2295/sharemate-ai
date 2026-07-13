import { Image } from 'expo-image';
import * as ImagePicker from 'expo-image-picker';
import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { AppButton } from '@/components/app-button';
import { EmptyState } from '@/components/empty-state';
import { InlineError } from '@/components/inline-error';
import { ReceiptAnalysisEditor } from '@/components/receipt-analysis-editor';
import { ScreenContainer } from '@/components/screen-container';
import { Radius, Spacing, Typography } from '@/constants/theme';
import { useAuth } from '@/contexts/auth-context';
import { useRoomTheme } from '@/hooks/use-room-theme';
import { apiRequest } from '@/services/api';
import type { ReceiptAnalysis } from '@/types/api';

export default function SettlementScreen() {
  const colors = useRoomTheme();
  const { currentHouse, token } = useAuth();
  const [selectedImage, setSelectedImage] = useState<ImagePicker.ImagePickerAsset | null>(null);
  const [analysis, setAnalysis] = useState<ReceiptAnalysis | null>(null);
  const [analysisRevision, setAnalysisRevision] = useState(0);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pickReceipt = async () => {
    setError(null);
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) { setError('영수증을 선택하려면 iPhone 설정에서 사진 접근을 허용해주세요.'); return; }
    const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], allowsMultipleSelection: false, quality: 0.85 });
    if (result.canceled) return;
    setSelectedImage(result.assets[0]); setAnalysis(null);
  };

  const analyzeReceipt = async () => {
    if (!selectedImage || !token || !currentHouse) { setError('분석할 영수증 이미지와 하우스를 확인해주세요.'); return; }
    const formData = new FormData();
    formData.append('file', { uri: selectedImage.uri, name: selectedImage.fileName || `receipt-${Date.now()}.jpg`, type: selectedImage.mimeType || 'image/jpeg' } as unknown as Blob);
    setAnalyzing(true); setError(null);
    try {
      const result = await apiRequest<ReceiptAnalysis>(`/houses/${currentHouse.id}/receipts/analyze`, { method: 'POST', token, body: formData });
      setAnalysis(result); setAnalysisRevision((revision) => revision + 1);
    } catch (requestError) {
      setAnalysis(null); setError(requestError instanceof Error ? requestError.message : '영수증을 분석하지 못했습니다.');
    } finally { setAnalyzing(false); }
  };

  return (
    <ScreenContainer keyboardAware subtitle="영수증을 등록하고 공동 지출을 확인하세요." title="정산">
      <View style={styles.uploadSection}>
        <View style={styles.sectionHeading}><Text style={[Typography.sectionTitle, { color: colors.textPrimary }]}>영수증 분석</Text><Text style={[styles.description, { color: colors.textSecondary }]}>사진에서 품목과 금액을 읽어옵니다.</Text></View>
        <AppButton icon="add-a-photo" label={selectedImage ? '다른 영수증 선택' : '영수증 등록'} onPress={pickReceipt} />
        {error ? <InlineError message={error} /> : null}
        {selectedImage ? (
          <View style={[styles.preview, { backgroundColor: colors.surface, borderColor: colors.border }]}>
            <Image accessibilityLabel="선택한 영수증 미리보기" contentFit="contain" source={{ uri: selectedImage.uri }} style={[styles.previewImage, { backgroundColor: colors.background }]} />
            <Text numberOfLines={1} style={[styles.fileName, { color: colors.textPrimary }]}>{selectedImage.fileName || '선택한 영수증 이미지'}</Text>
            <Text style={[styles.previewDescription, { color: colors.textSecondary }]}>이미지를 확인한 후 분석을 시작하세요.</Text>
            <AppButton disabled={analyzing} label="AI로 영수증 분석" loading={analyzing} onPress={analyzeReceipt} variant="secondary" />
          </View>
        ) : <Text style={[styles.helper, { color: colors.textSecondary }]}>JPG, PNG, HEIC 등 사진 보관함의 이미지를 선택할 수 있어요.</Text>}
      </View>

      {analysis ? <View style={styles.section}><View style={styles.sectionHeading}><Text style={[Typography.sectionTitle, { color: colors.textPrimary }]}>분석 결과</Text><Text style={[styles.description, { color: colors.textSecondary }]}>품목명, 수량과 금액을 직접 수정할 수 있어요.</Text></View><ReceiptAnalysisEditor key={analysisRevision} analysis={analysis} onChange={setAnalysis} /></View> : null}

      <View style={styles.section}>
        <View style={styles.sectionHeading}><Text style={[Typography.sectionTitle, { color: colors.textPrimary }]}>진행 중 정산</Text><Text style={[styles.description, { color: colors.textSecondary }]}>확인이 필요한 내역입니다.</Text></View>
        <EmptyState description="실제 정산 저장 API가 연결되면 이곳에 표시됩니다." icon="receipt-long" title="진행 중인 정산이 없어요" />
      </View>

      <View style={styles.section}>
        <Text style={[Typography.sectionTitle, { color: colors.textPrimary }]}>완료된 정산</Text>
        <EmptyState description="완료된 실제 정산 내역이 없습니다." icon="check-circle" title="완료 내역이 없어요" />
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  uploadSection: { gap: Spacing.item }, section: { gap: Spacing.item }, sectionHeading: { gap: 5 }, description: { fontSize: 13, lineHeight: 19 },
  preview: { borderRadius: Radius.card, borderWidth: 1, padding: Spacing.item }, previewImage: { borderRadius: Radius.input, height: 250, marginBottom: Spacing.item, width: '100%' },
  fileName: { fontSize: 14, fontWeight: '700' }, previewDescription: { fontSize: 12, marginBottom: Spacing.item, marginTop: 4 }, helper: { fontSize: 12, lineHeight: 18, textAlign: 'center' },
});
