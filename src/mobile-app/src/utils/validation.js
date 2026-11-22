// Same limits as the web UI and the REST API (spring.servlet.multipart.max-file-size)
export const MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024; // 20 MB
export const MAX_TITLE_LENGTH = 255;
export const MAX_CATEGORY_NAME_LENGTH = 100;

/**
 * @param file picked file { name, size, mimeType } or null
 * @returns field errors, e.g. { file: '...' }; empty object when valid
 */
export function validateUploadForm({ file, title }) {
  const errors = {};

  if (!file) {
    errors.file = 'Please choose a PDF to upload.';
  } else if (file.mimeType !== 'application/pdf' && !file.name?.toLowerCase().endsWith('.pdf')) {
    errors.file = 'Only PDF files are supported.';
  } else if (typeof file.size === 'number' && file.size > MAX_FILE_SIZE_BYTES) {
    // size can be missing for some file providers; the server still enforces the limit (413)
    errors.file = `File is too large. Maximum size is ${MAX_FILE_SIZE_BYTES / (1024 * 1024)} MB.`;
  }

  if (title && title.trim().length > MAX_TITLE_LENGTH) {
    errors.title = `Title must be at most ${MAX_TITLE_LENGTH} characters.`;
  }

  return errors;
}

export function validateTitle(title) {
  const trimmed = (title || '').trim();
  if (!trimmed) return 'Title is required.';
  if (trimmed.length > MAX_TITLE_LENGTH) return `Title must be at most ${MAX_TITLE_LENGTH} characters.`;
  return null;
}

export function validateCategoryName(name) {
  const trimmed = (name || '').trim();
  if (!trimmed) return 'Category name is required.';
  if (trimmed.length > MAX_CATEGORY_NAME_LENGTH) {
    return `Category name must be at most ${MAX_CATEGORY_NAME_LENGTH} characters.`;
  }
  return null;
}
