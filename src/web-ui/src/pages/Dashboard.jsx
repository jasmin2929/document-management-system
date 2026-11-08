import { useCallback, useEffect, useState } from 'react';
import { getAllCategories } from '../api/categories';
import { getAllDocuments, searchDocuments } from '../api/documents';
import CategoryBar from '../components/CategoryBar';
import DocumentList from '../components/DocumentList';
import UploadDialog from '../components/UploadDialog';
import { FILTER_ALL, FILTER_NONE, matchesFilter } from '../utils/filters';

export default function Dashboard() {
  const [categories, setCategories] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [filter, setFilter] = useState(FILTER_ALL);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [searchResult, setSearchResult] = useState(null);
  const [searching, setSearching] = useState(false);

  const loadCategories = useCallback(async () => {
    setCategories(await getAllCategories());
  }, []);

  const loadDocuments = useCallback(async () => {
    setDocuments(await getAllDocuments());
  }, []);

  const reload = useCallback(async (loader) => {
    setLoadError(null);
    try {
      await loader();
    } catch (error) {
      setLoadError(error.message);
    }
  }, []);

  useEffect(() => {
    Promise.all([getAllCategories(), getAllDocuments()])
      .then(([cats, docs]) => {
        setCategories(cats);
        setDocuments(docs);
      })
      .catch((error) => setLoadError(error.message))
      .finally(() => setLoading(false));
  }, []);

  const closeUpload = useCallback(() => setUploadOpen(false), []);

  function handleUploaded() {
    setUploadOpen(false);
    reload(loadDocuments);
  }

  async function handleSearch(event) {
    event.preventDefault();
    const term = query.trim();
    if (!term) {
      setSearchResult(null);
      return;
    }
    setSearching(true);
    setLoadError(null);
    try {
      setSearchResult({ term, documents: await searchDocuments(term) });
    } catch (error) {
      setLoadError(error.message);
    } finally {
      setSearching(false);
    }
  }

  const listedDocuments = searchResult ? searchResult.documents : documents;
  const visibleDocuments = listedDocuments.filter((document) => matchesFilter(document, filter));
  let emptyMessage = filter === FILTER_ALL ? 'No documents yet.' : 'No documents in this category.';
  if (searchResult) emptyMessage = `No documents match "${searchResult.term}".`;
  const defaultUploadCategory = filter !== FILTER_ALL && filter !== FILTER_NONE ? filter : '';

  return (
    <main className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <div className="page-subtitle">
            {searchResult
              ? `${searchResult.documents.length} ${searchResult.documents.length === 1 ? 'result' : 'results'} for "${searchResult.term}"`
              : `${documents.length} ${documents.length === 1 ? 'document' : 'documents'}`}
          </div>
        </div>
        <div className="page-header__actions">
          <form className="search-form" role="search" onSubmit={handleSearch}>
            <input
              type="search"
              className="input"
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                if (!event.target.value) setSearchResult(null);
              }}
              placeholder="Search document text"
              aria-label="Search document text"
            />
            <button type="submit" className="btn btn--secondary" disabled={searching}>
              {searching ? 'Searching…' : 'Search'}
            </button>
          </form>
          <button type="button" className="btn btn--primary" onClick={() => setUploadOpen(true)}>
            Upload document
          </button>
        </div>
      </div>

      <CategoryBar
        categories={categories}
        documents={documents}
        filter={filter}
        onFilterChange={setFilter}
        onCategoryCreated={() => reload(loadCategories)}
      />

      {loadError && (
        <div className="alert" role="alert">
          {loadError}
        </div>
      )}

      {loading ? (
        <p className="muted">Loading…</p>
      ) : (
        <DocumentList
          documents={visibleDocuments}
          emptyMessage={emptyMessage}
        />
      )}

      {uploadOpen && (
        <UploadDialog
          categories={categories}
          defaultCategoryId={defaultUploadCategory}
          onClose={closeUpload}
          onUploaded={handleUploaded}
        />
      )}
    </main>
  );
}
