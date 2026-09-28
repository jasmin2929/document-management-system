import { apiDelete, apiGet, apiPost, apiPut } from './client';

export function getAllCategories() {
  return apiGet('/categories');
}

export function getCategoryById(id) {
  return apiGet(`/categories/${id}`);
}

export function createCategory(name) {
  return apiPost('/categories', { name });
}

export function updateCategory(id, name) {
  return apiPut(`/categories/${id}`, { name });
}

export function deleteCategory(id) {
  return apiDelete(`/categories/${id}`);
}
