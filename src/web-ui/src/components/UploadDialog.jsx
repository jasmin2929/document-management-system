import { useEffect, useState } from 'react';
import { uploadDocument } from '../api/documents';
import { formatFileSize } from '../utils/format';
import { MAX_FILE_SIZE_BYTES, validateUploadForm } from '../utils/validation';

export default function UploadDialog({ categories, defaultCategoryId, onClose, onUploaded }) {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [categoryId, setCategoryId] = useState(defaultCategoryId || '');
  const [fieldErrors, setFieldErrors] = useState({});
  const [submitError, setSubmitError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === 'Escape' && !submitting) onClose();
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose, submitting]);

  function selectFile(selected) {
    setFile(selected || null);
    setFieldErrors((prev) => ({ ...prev, file: undefined }));
  }

  function handleDrop(event) {
    event.preventDefault();
    setDragActive(false);
    selectFile(event.dataTransfer.files[0]);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitError(null);

    const errors = validateUploadForm({ file, title });
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setSubmitting(true);
    try {
      await uploadDocument({ file, title: title.trim(), categoryId });
      onUploaded();
    } catch (error) {
      setSubmitError(error.message);
      setSubmitting(false);
    }
  }

  const dropzoneClass = [
    'dropzone',
    dragActive && 'dropzone--active',
    fieldErrors.file && 'dropzone--invalid',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className="dialog-backdrop" onClick={() => !submitting && onClose()}>
      <form
        className="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="upload-dialog-title"
        onClick={(event) => event.stopPropagation()}
        onSubmit={handleSubmit}
        noValidate
      >
        <div className="dialog__header">
          <h2 id="upload-dialog-title" className="dialog__title">
            Upload document
          </h2>
          <button type="button" className="dialog__close" onClick={onClose} disabled={submitting} aria-label="Close">
            ×
          </button>
        </div>

        <div>
          <label
            className={dropzoneClass}
            onDragOver={(event) => {
              event.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
          >
            <input type="file" accept=".pdf,application/pdf" onChange={(event) => selectFile(event.target.files[0])} />
            <span className="dropzone__label">{file ? file.name : 'Choose a PDF or drop it here'}</span>
            <span className="dropzone__hint">
              {file
                ? formatFileSize(file.size)
                : `PDF, max ${MAX_FILE_SIZE_BYTES / (1024 * 1024)} MB`}
            </span>
          </label>
          {fieldErrors.file && (
            <div className="field-error dropzone__error" role="alert">
              {fieldErrors.file}
            </div>
          )}
        </div>

        <label className="field">
          Title
          <input
            className={`input${fieldErrors.title ? ' input--invalid' : ''}`}
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Optional — defaults to file name"
            aria-invalid={Boolean(fieldErrors.title)}
          />
          {fieldErrors.title && (
            <span className="field-error" role="alert">
              {fieldErrors.title}
            </span>
          )}
        </label>

        <label className="field">
          Category
          <select className="input" value={categoryId} onChange={(event) => setCategoryId(event.target.value)}>
            <option value="">None</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </label>

        {submitError && (
          <div className="alert" role="alert">
            {submitError}
          </div>
        )}

        <div className="dialog__actions">
          <button type="button" className="btn btn--secondary" onClick={onClose} disabled={submitting}>
            Cancel
          </button>
          <button type="submit" className="btn btn--primary" disabled={!file || submitting}>
            {submitting ? 'Uploading…' : 'Upload'}
          </button>
        </div>
      </form>
    </div>
  );
}
