import { apiDelete, apiGet, apiPut, apiUpload, fileUrl } from './client';

export function getAllDocuments(categoryId) {
  return apiGet('/documents', categoryId ? { categoryId } : undefined);
}

export function getDocumentById(id) {
  return apiGet(`/documents/${id}`);
}

export function uploadDocument({ file, title, categoryId }) {
  const formData = new FormData();
  formData.append('file', file);
  if (title) formData.append('title', title);
  if (categoryId) formData.append('categoryId', categoryId);
  return apiUpload('/documents/upload', formData);
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
