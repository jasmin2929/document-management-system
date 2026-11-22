import { Directory, File, Paths } from 'expo-file-system';
import { apiDelete, apiGet, apiPut, apiUpload, fileUrl } from './client';

export function getAllDocuments(categoryId) {
  return apiGet('/documents', categoryId ? { categoryId } : undefined);
}

export function searchDocuments(query) {
  return apiGet('/documents/search', { q: query });
}

export function getDocumentById(id) {
  return apiGet(`/documents/${id}`);
}

/**
 * The document picker stores its copy under a random name (e.g. "3F2A…E4.pdf"), and the multipart
 * filename is taken from the file itself. Without this step the server would use the random name as
 * title and original file name, so the file is copied under the name the user picked.
 */
async function withOriginalName(picked) {
  const source = new File(picked.uri);
  // "/" or "\" would create sub folders instead of a file name
  const name = picked.name?.trim().replace(/[/\\]/g, '_');
  if (!name || source.name === name) {
    return { file: source, temporary: false };
  }

  try {
    const directory = new Directory(Paths.cache, 'uploads');
    directory.create({ intermediates: true, idempotent: true });
    const target = new File(directory, name);
    if (target.exists) target.delete();
    await source.copy(target);
    return { file: target, temporary: true };
  } catch (error) {
    // the upload still works with the picker's copy, only the file name is not the original one
    console.warn('[upload] could not keep the original file name:', error);
    return { file: source, temporary: false };
  }
}

/**
 * @param file picked file from expo-document-picker: { uri, name, mimeType }
 */
export async function uploadDocument({ file, title, categoryId }) {
  const upload = await withOriginalName(file);
  try {
    const formData = new FormData();
    // Since Expo SDK 57 the global fetch is expo/fetch, which only accepts strings, Blobs or objects with
    // bytes() as form parts; React Native's classic { uri, name, type } part throws
    // "Unsupported FormDataPart implementation". expo-file-system's File implements Blob.
    formData.append('file', upload.file);
    if (title) formData.append('title', title);
    if (categoryId) formData.append('categoryId', String(categoryId));
    return await apiUpload('/documents/upload', formData);
  } finally {
    // the copy is only needed for the request; the cache would otherwise grow with every upload
    if (upload.temporary) {
      try {
        upload.file.delete();
      } catch {
        // not critical: the system clears the cache directory when storage runs low
      }
    }
  }
}

export function updateDocument(id, dto) {
  return apiPut(`/documents/${id}`, dto);
}

export function deleteDocument(id) {
  return apiDelete(`/documents/${id}`);
}

export function documentFileUrl(id) {
  return fileUrl(`/documents/${id}/file`);
}