export const MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024; // 20MB
export const MAX_TITLE_LENGTH = 255;

export function validateUploadForm({ file, title }) {
  const errors = {};

  if (!file) {
    errors.file = 'Please choose a file to upload.';
  } else {
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      errors.file = 'Only PDF files are supported.';
    } else if (file.size > MAX_FILE_SIZE_BYTES) {
      errors.file = `File is too large. Maximum size is ${MAX_FILE_SIZE_BYTES / (1024 * 1024)}MB.`;
    }
  }

  if (title && title.length > MAX_TITLE_LENGTH) {
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
  const errors = {};
  const trimmed = (name || '').trim();

  if (!trimmed) {
    errors.name = 'Category name is required.';
  } else if (trimmed.length > 100) {
    errors.name = 'Category name must be at most 100 characters.';
  }

  return errors;
}
