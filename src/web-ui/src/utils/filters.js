export const FILTER_ALL = 'all';
export const FILTER_NONE = 'none';

export function matchesFilter(document, filter) {
  if (filter === FILTER_ALL) return true;
  if (filter === FILTER_NONE) return !document.category;
  return String(document.category?.id) === filter;
}
