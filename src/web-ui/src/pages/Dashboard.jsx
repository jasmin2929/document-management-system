import { useCallback, useEffect, useState } from 'react';
import { getAllCategories } from '../api/categories';
import { getAllDocuments } from '../api/documents';
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

  const visibleDocuments = documents.filter((document) => matchesFilter(document, filter));
  const defaultUploadCategory = filter !== FILTER_ALL && filter !== FILTER_NONE ? filter : '';

  return (
    <main className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <div className="page-subtitle">
            {documents.length} {documents.length === 1 ? 'document' : 'documents'}
          </div>
        </div>
        <button type="button" className="btn btn--primary" onClick={() => setUploadOpen(true)}>
          Upload document
        </button>
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
          emptyMessage={filter === FILTER_ALL ? 'No documents yet.' : 'No documents in this category.'}
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
