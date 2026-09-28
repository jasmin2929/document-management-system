import { useState } from 'react';
import { uploadDocument } from '../api/documents';
import { validateUploadForm } from '../utils/validation';

const initialState = { file: null, title: '', categoryId: '' };

export default function UploadForm({ categories, onUploaded }) {
  const [values, setValues] = useState(initialState);
  const [fieldErrors, setFieldErrors] = useState({});
  const [submitError, setSubmitError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [fileInputKey, setFileInputKey] = useState(0);

  function handleFileChange(event) {
    setValues((prev) => ({ ...prev, file: event.target.files[0] || null }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitError(null);

    const errors = validateUploadForm(values);
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      return;
    }

    setSubmitting(true);
    try {
      await uploadDocument(values);
      setValues(initialState);
      setFieldErrors({});
      setFileInputKey((key) => key + 1);
      onUploaded();
    } catch (error) {
      setSubmitError(error.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <h2>Upload document</h2>

      <div>
        <label htmlFor="upload-file">File (PDF, max 20MB)</label>
        <br />
        <input
          key={fileInputKey}
          id="upload-file"
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleFileChange}
        />
        {fieldErrors.file && <div role="alert">{fieldErrors.file}</div>}
      </div>

      <div>
        <label htmlFor="upload-title">Title (optional)</label>
        <br />
        <input
          id="upload-title"
          type="text"
          value={values.title}
          onChange={(event) => setValues((prev) => ({ ...prev, title: event.target.value }))}
        />
        {fieldErrors.title && <div role="alert">{fieldErrors.title}</div>}
      </div>

      <div>
        <label htmlFor="upload-category">Category (optional)</label>
        <br />
        <select
          id="upload-category"
          value={values.categoryId}
          onChange={(event) => setValues((prev) => ({ ...prev, categoryId: event.target.value }))}
        >
          <option value="">None</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </div>

      {submitError && <div role="alert">{submitError}</div>}

      <button type="submit" disabled={submitting}>
        {submitting ? 'Uploading…' : 'Upload'}
      </button>
    </form>
  );
}
