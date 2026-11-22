import { useCallback, useRef, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, RefreshControl, StyleSheet, Text, TextInput, View } from 'react-native';
import { Stack, useFocusEffect, useRouter } from 'expo-router';
import { getAllCategories } from '../src/api/categories';
import { getAllDocuments, searchDocuments } from '../src/api/documents';
import Button from '../src/components/Button';
import CategoryChips from '../src/components/CategoryChips';
import DocumentRow from '../src/components/DocumentRow';
import ErrorBanner from '../src/components/ErrorBanner';
import NewCategoryForm from '../src/components/NewCategoryForm';
import { colors, radius, spacing, typography } from '../src/theme';
import { FILTER_ALL, FILTER_NONE, buildFilterChips, matchesFilter } from '../src/utils/filters';

export default function DashboardScreen() {
  const router = useRouter();

  const [categories, setCategories] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [filter, setFilter] = useState(FILTER_ALL);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadError, setLoadError] = useState(null);

  const [query, setQuery] = useState('');
  const [searchResult, setSearchResult] = useState(null);
  const [searching, setSearching] = useState(false);
  // read inside load(); a ref keeps load() stable, so the focus effect does not re-run on every search
  const activeSearchTerm = useRef(null);

  const load = useCallback(async () => {
    setLoadError(null);
    try {
      const [loadedCategories, loadedDocuments] = await Promise.all([getAllCategories(), getAllDocuments()]);
      setCategories(loadedCategories);
      setDocuments(loadedDocuments);

      // keep an active search up to date as well (e.g. after a document was deleted)
      const term = activeSearchTerm.current;
      if (term) {
        setSearchResult({ term, documents: await searchDocuments(term) });
      }
    } catch (error) {
      setLoadError(error.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // reload whenever the screen becomes visible again: after upload, title/category change or delete
  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  async function handleRefresh() {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }

  function clearSearch() {
    activeSearchTerm.current = null;
    setSearchResult(null);
  }

  async function handleSearch() {
    const term = query.trim();
    if (!term) {
      clearSearch();
      return;
    }

    setSearching(true);
    setLoadError(null);
    try {
      const found = await searchDocuments(term);
      activeSearchTerm.current = term;
      setSearchResult({ term, documents: found });
    } catch (error) {
      // e.g. 503 "Search is currently not available" when Elasticsearch is down
      setLoadError(error.message);
    } finally {
      setSearching(false);
    }
  }

  function openUpload() {
    // preselect the category that is currently filtered, like the web UI
    const categoryId = filter !== FILTER_ALL && filter !== FILTER_NONE ? filter : undefined;
    router.push({ pathname: '/upload', params: categoryId ? { categoryId } : {} });
  }

  const listedDocuments = searchResult ? searchResult.documents : documents;
  const visibleDocuments = listedDocuments.filter((document) => matchesFilter(document, filter));

  let emptyMessage = filter === FILTER_ALL ? 'No documents yet.' : 'No documents in this category.';
  if (searchResult) emptyMessage = `No documents match "${searchResult.term}".`;

  const subtitle = searchResult
    ? `${searchResult.documents.length} ${searchResult.documents.length === 1 ? 'result' : 'results'} for "${searchResult.term}"`
    : `${documents.length} ${documents.length === 1 ? 'document' : 'documents'}`;

  // passed as an element (not a component), so the search field keeps focus while typing
  const listHeader = (
    <View style={styles.header}>
      <View style={styles.searchRow}>
        <TextInput
          style={styles.searchInput}
          value={query}
          onChangeText={(text) => {
            setQuery(text);
            if (!text) clearSearch();
          }}
          onSubmitEditing={handleSearch}
          placeholder="Search document text"
          placeholderTextColor={colors.muted}
          returnKeyType="search"
          clearButtonMode="while-editing"
          autoCapitalize="none"
          autoCorrect={false}
          accessibilityLabel="Search document text"
        />
        <Button title="Search" variant="secondary" onPress={handleSearch} loading={searching} />
      </View>

      <Text style={typography.small}>{subtitle}</Text>

      <CategoryChips chips={buildFilterChips(categories, documents)} selectedKey={filter} onSelect={setFilter} />
      <NewCategoryForm onCreated={load} />
      <ErrorBanner message={loadError} />
    </View>
  );

  return (
    <>
      <Stack.Screen
        options={{
          headerRight: () => (
            <Pressable onPress={openUpload} hitSlop={12} accessibilityRole="button" accessibilityLabel="Upload document">
              <Text style={styles.headerAction}>Upload</Text>
            </Pressable>
          ),
        }}
      />
      <FlatList
        data={visibleDocuments}
        keyExtractor={(document) => String(document.id)}
        renderItem={({ item }) => <DocumentRow document={item} onPress={() => router.push(`/documents/${item.id}`)} />}
        ListHeaderComponent={listHeader}
        ListEmptyComponent={
          loading ? (
            <ActivityIndicator style={styles.empty} />
          ) : (
            <Text style={[typography.small, styles.empty]}>{emptyMessage}</Text>
          )
        }
        ItemSeparatorComponent={() => <View style={styles.separator} />}
        contentContainerStyle={styles.content}
        contentInsetAdjustmentBehavior="automatic"
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="on-drag"
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />}
      />
    </>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.lg, paddingBottom: spacing.xl * 2 },
  header: { gap: spacing.md, marginBottom: spacing.md },
  searchRow: { flexDirection: 'row', gap: spacing.sm },
  searchInput: {
    flex: 1,
    minHeight: 44,
    paddingHorizontal: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    fontSize: 15,
    color: colors.text,
  },
  separator: { height: spacing.sm },
  empty: { textAlign: 'center', marginTop: spacing.xl },
  headerAction: { color: colors.primary, fontSize: 17, fontWeight: '600' },
});
