import { useCallback, useEffect, useState } from 'react';
import { getAllCategories } from '../api/categories';
import { getAllDocuments } from '../api/documents';
import CategoryManager from '../components/CategoryManager';
import DocumentList from '../components/DocumentList';
import UploadForm from '../components/UploadForm';

export default function Dashboard() {
  const [categories, setCategories] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);

  const loadCategories = useCallback(async () => {
    const data = await getAllCategories();
    setCategories(data);
  }, []);

  const loadDocuments = useCallback(async (categoryId) => {
    const data = await getAllDocuments(categoryId || undefined);
    setDocuments(data);
  }, []);

  const refreshAll = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      await Promise.all([loadCategories(), loadDocuments(selectedCategoryId)]);
    } catch (error) {
      setLoadError(error.message);
    } finally {
      setLoading(false);
    }
  }, [loadCategories, loadDocuments, selectedCategoryId]);

  useEffect(() => {
    refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCategoryId]);

  async function handleCategoryCreated() {
    try {
      await loadCategories();
    } catch (error) {
      setLoadError(error.message);
    }
  }

  async function handleDocumentUploaded() {
    try {
      await loadDocuments(selectedCategoryId);
    } catch (error) {
      setLoadError(error.message);
    }
  }

  return (
    <section>
      <h1>Dashboard</h1>

      <CategoryManager
        categories={categories}
        selectedCategoryId={selectedCategoryId}
        onSelectCategory={setSelectedCategoryId}
        onCategoryCreated={handleCategoryCreated}
      />

      <UploadForm categories={categories} onUploaded={handleDocumentUploaded} />

      <h2>Documents</h2>
      {loadError && <div role="alert">{loadError}</div>}
      {loading ? <p>Loading…</p> : <DocumentList documents={documents} />}
    </section>
  );
}
