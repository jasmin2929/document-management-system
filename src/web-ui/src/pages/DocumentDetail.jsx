import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { getAllCategories } from '../api/categories';
import { deleteDocument, documentFileUrl, getDocumentById, updateDocument } from '../api/documents';
import StatusBadge from '../components/StatusBadge';
import { formatDate, formatFileSize, formatStatus } from '../utils/format';
import { validateTitle } from '../utils/validation';

// ID keying/filtering for fresh remounts
export default function DocumentDetailRoute() {
  const { id } = useParams();
  return <DocumentDetail key={id} id={id} />;
}

function DocumentDetail({ id }) {
  const navigate = useNavigate();

  const [doc, setDoc] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [notFound, setNotFound] = useState(false);

  const [titleDraft, setTitleDraft] = useState('');
  const [titleError, setTitleError] = useState(null);
  const [saveState, setSaveState] = useState({ status: 'idle' });
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    let ignore = false;

    Promise.all([getDocumentById(id), getAllCategories()])
      .then(([doc, cats]) => {
        if (ignore) return;
        setDoc(doc);
        setTitleDraft(doc.title);
        setCategories(cats);
      })
      .catch((error) => {
        if (ignore) return;
        if (error.status === 404) setNotFound(true);
        else setLoadError(error.message);
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });

    return () => {
      ignore = true;
    };
  }, [id]);

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

  function handleCategoryChange(event) {
    const value = event.target.value;
    save(value ? { categoryId: Number(value) } : { clearCategory: true });
  }

  async function handleDelete() {
    if (!window.confirm(`Delete "${doc.title}"? This cannot be undone.`)) return;

    setDeleting(true);
    try {
      await deleteDocument(id);
      navigate('/');
    } catch (error) {
      setSaveState({ status: 'error', message: error.message });
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <main className="page page--detail">
        <p className="muted">Loading…</p>
      </main>
    );
  }

  if (notFound || loadError) {
    return (
      <main className="page page--detail">
        <Breadcrumb current={notFound ? 'Not found' : 'Error'} />
        <h1 className="detail-title">{notFound ? 'Document not found' : 'Could not load document'}</h1>
        <p className="muted">
          {notFound ? `There is no document with ID ${id}.` : loadError}{' '}
          <Link to="/">Back to dashboard</Link>
        </p>
      </main>
    );
  }

  const fileUrl = documentFileUrl(doc.id);
  const isPdf = doc.fileType === 'application/pdf';

  return (
    <main className="page page--detail">
      <Breadcrumb current={doc.title} />

      <div className="detail-header">
        <div className="detail-header__main">
          <h1 className="detail-title">{doc.title}</h1>
          <div className="detail-meta">
            <StatusBadge status={doc.status} />
            <span>{doc.originalFileName}</span>
          </div>
        </div>
        <div className="detail-actions">
          <button type="button" className="btn btn--danger" onClick={handleDelete} disabled={deleting}>
            {deleting ? 'Deleting…' : 'Delete'}
          </button>
          <a className="btn btn--primary" href={fileUrl} download={doc.originalFileName}>
            {isPdf ? 'Download PDF' : 'Download'}
          </a>
        </div>
      </div>

      <div className="detail-grid">
        <div className="card preview">
          {isPdf ? (
            <iframe className="preview__frame" src={fileUrl} title={`Preview of ${doc.title}`} />
          ) : (
            <div className="preview__frame preview__placeholder">Preview not available</div>
          )}
        </div>

        <aside className="card details-panel">
          <div className="details-panel__heading">Details</div>

          <label className="field">
            Title
            <input
              className={`input${titleError ? ' input--invalid' : ''}`}
              value={titleDraft}
              onChange={(event) => {
                setTitleDraft(event.target.value);
                setTitleError(null);
              }}
              onKeyDown={(event) => {
                if (event.key === 'Enter') event.currentTarget.blur();
              }}
              onBlur={commitTitle}
              aria-invalid={Boolean(titleError)}
            />
            {titleError && (
              <span className="field-error" role="alert">
                {titleError}
              </span>
            )}
          </label>

          <label className="field">
            Category
            <select
              className="input"
              value={doc.category?.id ?? ''}
              onChange={handleCategoryChange}
              disabled={saveState.status === 'saving'}
            >
              <option value="">None</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </label>

          <SaveIndicator state={saveState} />

          <div className="details-panel__divider" />

          <dl className="meta-list">
            <dt>Status</dt>
            <dd>{formatStatus(doc.status)}</dd>
            <dt>Size</dt>
            <dd className="meta-list__mono">{formatFileSize(doc.fileSize)}</dd>
            <dt>Uploaded</dt>
            <dd>{formatDate(doc.uploadDate, { withSeconds: true })}</dd>
            {doc.lastModifiedDate && (
              <>
                <dt>Modified</dt>
                <dd>{formatDate(doc.lastModifiedDate, { withSeconds: true })}</dd>
              </>
            )}
            <dt>File</dt>
            <dd>{doc.originalFileName}</dd>
          </dl>
        </aside>
      </div>
    </main>
  );
}

function Breadcrumb({ current }) {
  return (
    <nav className="breadcrumb" aria-label="Breadcrumb">
      <Link to="/">Dashboard</Link>
      <span aria-hidden="true">/</span>
      <span className="breadcrumb__current" aria-current="page">
        {current}
      </span>
    </nav>
  );
}

function SaveIndicator({ state }) {
  if (state.status === 'error') {
    return (
      <div className="field-error" role="alert">
        {state.message}
      </div>
    );
  }
  const text = { saving: 'Saving…', saved: 'All changes saved' }[state.status] || '';
  return (
    <div className="save-state" aria-live="polite">
      {text}
    </div>
  );
}
