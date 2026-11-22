import { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import { Stack, useLocalSearchParams, useRouter } from 'expo-router';
import { getAllCategories } from '../src/api/categories';
import { uploadDocument } from '../src/api/documents';
import Button from '../src/components/Button';
import CategoryChips from '../src/components/CategoryChips';
import ErrorBanner from '../src/components/ErrorBanner';
import { colors, radius, spacing, typography } from '../src/theme';
import { FILTER_NONE, buildCategoryChoices } from '../src/utils/filters';
import { formatFileSize } from '../src/utils/format';
import { MAX_FILE_SIZE_BYTES, validateUploadForm } from '../src/utils/validation';

export default function UploadScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();

  const [categories, setCategories] = useState([]);
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [categoryKey, setCategoryKey] = useState(
    typeof params.categoryId === 'string' ? params.categoryId : FILTER_NONE,
  );
  const [fieldErrors, setFieldErrors] = useState({});
  const [submitError, setSubmitError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    // the form still works without categories, so a failure only shows a message
    getAllCategories()
      .then(setCategories)
      .catch((error) => setSubmitError(error.message));
  }, []);

  async function pickFile() {
    try {
      // copyToCacheDirectory: the app gets a readable file:// URI, also for files from iCloud Drive
      const result = await DocumentPicker.getDocumentAsync({
        type: 'application/pdf',
        copyToCacheDirectory: true,
        multiple: false,
      });
      if (result.canceled) return;

      const asset = result.assets[0];
      setFile({ uri: asset.uri, name: asset.name, size: asset.size, mimeType: asset.mimeType });
      setFieldErrors((previous) => ({ ...previous, file: undefined }));
    } catch {
      setFieldErrors((previous) => ({ ...previous, file: 'The file could not be opened. Please choose another one.' }));
    }
  }

  async function handleSubmit() {
    setSubmitError(null);
    const errors = validateUploadForm({ file, title });
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setSubmitting(true);
    try {
      await uploadDocument({
        file,
        title: title.trim(),
        categoryId: categoryKey === FILTER_NONE ? undefined : categoryKey,
      });
      // the dashboard reloads on focus, so the new document shows up there
      router.back();
    } catch (error) {
      // e.g. 413 file too large, 503 broker unavailable, or the server not reachable
      setSubmitError(error.message);
      setSubmitting(false);
    }
  }

  return (
    <>
      {/* no swipe-to-dismiss while the upload is running */}
      <Stack.Screen options={{ gestureEnabled: !submitting }} />
      <ScrollView
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
        automaticallyAdjustKeyboardInsets
      >
        <View style={styles.field}>
          <Text style={typography.label}>PDF file</Text>
          <View style={[styles.fileBox, fieldErrors.file && styles.fileBoxInvalid]}>
            <Text style={typography.body} numberOfLines={2}>
              {file ? file.name : 'No file selected'}
            </Text>
            <Text style={typography.small}>
              {file ? formatFileSize(file.size) : `PDF, max ${MAX_FILE_SIZE_BYTES / (1024 * 1024)} MB`}
            </Text>
            <Button
              title={file ? 'Choose another PDF' : 'Choose PDF'}
              variant="secondary"
              onPress={pickFile}
              disabled={submitting}
            />
          </View>
          {fieldErrors.file && (
            <Text style={styles.error} accessibilityRole="alert">
              {fieldErrors.file}
            </Text>
          )}
        </View>

        <View style={styles.field}>
          <Text style={typography.label}>Title</Text>
          <TextInput
            style={[styles.input, fieldErrors.title && styles.inputInvalid]}
            value={title}
            onChangeText={setTitle}
            placeholder="Optional — defaults to file name"
            placeholderTextColor={colors.muted}
            editable={!submitting}
            accessibilityLabel="Title"
          />
          {fieldErrors.title && (
            <Text style={styles.error} accessibilityRole="alert">
              {fieldErrors.title}
            </Text>
          )}
        </View>

        <View style={styles.field}>
          <Text style={typography.label}>Category</Text>
          <CategoryChips
            chips={buildCategoryChoices(categories)}
            selectedKey={categoryKey}
            onSelect={setCategoryKey}
            disabled={submitting}
          />
        </View>

        <ErrorBanner message={submitError} />

        <View style={styles.actions}>
          <Button title="Cancel" variant="secondary" onPress={() => router.back()} disabled={submitting} style={styles.action} />
          <Button
            title="Upload"
            onPress={handleSubmit}
            disabled={!file}
            loading={submitting}
            style={styles.action}
          />
        </View>
      </ScrollView>
    </>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.lg, gap: spacing.lg },
  field: { gap: spacing.sm },
  fileBox: {
    gap: spacing.sm,
    padding: spacing.lg,
    borderRadius: radius.md,
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  fileBoxInvalid: { borderColor: colors.danger },
  input: {
    minHeight: 44,
    paddingHorizontal: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    fontSize: 15,
    color: colors.text,
  },
  inputInvalid: { borderColor: colors.danger },
  error: { color: colors.danger, fontSize: 13 },
  actions: { flexDirection: 'row', gap: spacing.sm },
  action: { flex: 1 },
});
