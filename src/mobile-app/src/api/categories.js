import { apiGet, apiPost } from './client';

export function getAllCategories() {
  return apiGet('/categories');
}

export function createCategory(name) {
  return apiPost('/categories', { name });
}
