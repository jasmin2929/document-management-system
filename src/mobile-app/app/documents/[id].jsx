import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Linking, RefreshControl, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { Stack, useLocalSearchParams, useRouter } from 'expo-router';
import { getAllCategories } from '../../src/api/categories';
import { deleteDocument, documentFileUrl, getDocumentById, updateDocument } from '../../src/api/documents';
import Button from '../../src/components/Button';
import CategoryChips from '../../src/components/CategoryChips';
import ErrorBanner from '../../src/components/ErrorBanner';
import StatusBadge from '../../src/components/StatusBadge';
import { colors, radius, spacing, typography } from '../../src/theme';
import { FILTER_NONE, buildCategoryChoices } from '../../src/utils/filters';
import { formatDate, formatFileSize, formatStatus } from '../../src/utils/format';
import { validateTitle } from '../../src/utils/validation';

export default function DocumentDetailScreen() {
  const { id } = useLocalSearchParams();
  const router = useRouter();

  const [doc, setDoc] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadError, setLoadError] = useState(null);
  const [notFound, setNotFound] = useState(false);

  const [titleDraft, setTitleDraft] = useState('');
  const [titleError, setTitleError] = useState(null);
  const [saveState, setSaveState] = useState({ status: 'idle' });
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    try {
      const [loadedDoc, loadedCategories] = await Promise.all([getDocumentById(id), getAllCategories()]);
      setDoc(loadedDoc);
      setTitleDraft(loadedDoc.title);
      setCategories(loadedCategories);
      setLoadError(null);
    } catch (error) {
      if (error.status === 404) setNotFound(true);
      else setLoadError(error.message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  // OCR and summary run asynchronously, pull-to-refresh shows their latest state
  async function handleRefresh() {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }

  async function save(patch) {
    setSaveState({ status: 'saving' });
    try {
      const updated = await updateDocument(id, patch);
      setDoc(updated);
      setTitleDraft(updated.title);
      setSaveState({ status: 'saved' });
    } catch (error) {
      setSaveState({ status: 'error', message: error.message });
    }
  }

  function commitTitle() {
    const error = validateTitle(titleDraft);
    setTitleError(error);
    if (error) return;

    const trimmed = titleDraft.trim();
    if (trimmed === doc.title) {
      setTitleDraft(trimmed);
      return;
    }
    save({ title: trimmed });
  }

  function handleCategorySelect(key) {
    const currentKey = doc.category ? String(doc.category.id) : FILTER_NONE;
    if (key === currentKey) return;
    save(key === FILTER_NONE ? { clearCategory: true } : { categoryId: Number(key) });
  }

  async function openFile() {
    try {
      // Safari shows the PDF; it is served by the REST API through nginx
      await Linking.openURL(documentFileUrl(doc.id));
    } catch {
      setSaveState({ status: 'error', message: 'The file could not be opened.' });
    }
  }

  function confirmDelete() {
    Alert.alert('Delete document', `Delete "${doc.title}"? This cannot be undone.`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: handleDelete },
    ]);
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await deleteDocument(id);
      // the dashboard reloads on focus, so the document disappears there
      router.back();
    } catch (error) {
      setSaveState({ status: 'error', message: error.message });
      setDeleting(false);
    }
  }

  if (loading) {
    return <ActivityIndicator style={styles.centered} />;
  }

  if (notFound || loadError) {
    return (
      <View style={styles.content}>
        <Stack.Screen options={{ title: notFound ? 'Not found' : 'Error' }} />
        <Text style={typography.title}>{notFound ? 'Document not found' : 'Could not load document'}</Text>
        <Text style={typography.small}>{notFound ? `There is no document with ID ${id}.` : loadError}</Text>
        {!notFound && <Button title="Try again" variant="secondary" onPress={handleRefresh} loading={refreshing} />}
      </View>
    );
  }

  const busy = saveState.status === 'saving' || deleting;

  return (
    <>
      <Stack.Screen options={{ title: doc.title }} />
      <ScrollView
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
        automaticallyAdjustKeyboardInsets
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />}
      >
        <View style={styles.headerRow}>
          <StatusBadge status={doc.status} />
          <Text style={typography.small} numberOfLines={1}>
            {doc.originalFileName}
          </Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardHeading}>Summary</Text>
          <Text style={doc.summary ? typography.body : typography.small}>
            {doc.summary || summaryPlaceholder(doc.status)}
          </Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardHeading}>Details</Text>

          <View style={styles.field}>
            <Text style={typography.label}>Title</Text>
            <TextInput
              style={[styles.input, titleError && styles.inputInvalid]}
              value={titleDraft}
              onChangeText={(text) => {
                setTitleDraft(text);
                setTitleError(null);
              }}
              // fires on "done" and when the field loses focus, like onBlur in the web UI
              onEndEditing={commitTitle}
              returnKeyType="done"
              editable={!busy}
              accessibilityLabel="Title"
            />
            {titleError && (
              <Text style={styles.error} accessibilityRole="alert">
                {titleError}
              </Text>
            )}
          </View>

          <View style={styles.field}>
            <Text style={typography.label}>Category</Text>
            <CategoryChips
              chips={buildCategoryChoices(categories)}
              selectedKey={doc.category ? String(doc.category.id) : FILTER_NONE}
              onSelect={handleCategorySelect}
              disabled={busy}
            />
          </View>

          <SaveIndicator state={saveState} />

          <View style={styles.divider} />

          <MetaRow label="Status" value={formatStatus(doc.status)} />
          <MetaRow label="Size" value={formatFileSize(doc.fileSize)} />
          <MetaRow label="Uploaded" value={formatDate(doc.uploadDate, { withSeconds: true })} />
          {doc.lastModifiedDate && (
            <MetaRow label="Modified" value={formatDate(doc.lastModifiedDate, { withSeconds: true })} />
          )}
          <MetaRow label="File" value={doc.originalFileName} />
        </View>

        <View style={styles.actions}>
          <Button title="Delete" variant="danger" onPress={confirmDelete} loading={deleting} style={styles.action} />
          <Button
            title={doc.fileType === 'application/pdf' ? 'Open PDF' : 'Open file'}
            onPress={openFile}
            disabled={deleting}
            style={styles.action}
          />
        </View>
      </ScrollView>
    </>
  );
}

function summaryPlaceholder(status) {
  if (status === 'PENDING' || status === 'PROCESSING') {
    return 'The summary is created after text recognition. Pull down to refresh.';
  }
  if (status === 'FAILED') {
    return 'No summary: text recognition failed for this document.';
  }
  return 'No summary available yet. Pull down to refresh.';
}

function MetaRow({ label, value }) {
  return (
    <View style={styles.metaRow}>
      <Text style={typography.small}>{label}</Text>
      <Text style={styles.metaValue} numberOfLines={2}>
        {value}
      </Text>
    </View>
  );
}

function SaveIndicator({ state }) {
  if (state.status === 'error') {
    return <ErrorBanner message={state.message} />;
  }
  const text = { saving: 'Saving…', saved: 'All changes saved' }[state.status];
  return text ? (
    <Text style={typography.small} accessibilityLiveRegion="polite">
      {text}
    </Text>
  ) : null;
}

const styles = StyleSheet.create({
  centered: { flex: 1, justifyContent: 'center' },
  content: { padding: spacing.lg, gap: spacing.lg },
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  card: {
    gap: spacing.md,
    padding: spacing.lg,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardHeading: { fontSize: 16, fontWeight: '700', color: colors.text },
  field: { gap: spacing.sm },
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
  divider: { height: 1, backgroundColor: colors.border },
  metaRow: { flexDirection: 'row', justifyContent: 'space-between', gap: spacing.lg },
  metaValue: { flexShrink: 1, textAlign: 'right', fontSize: 14, color: colors.text },
  actions: { flexDirection: 'row', gap: spacing.sm },
  action: { flex: 1 },
});
