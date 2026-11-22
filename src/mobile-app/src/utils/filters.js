export const FILTER_ALL = 'all';
export const FILTER_NONE = 'none';

export function matchesFilter(document, filter) {
  if (filter === FILTER_ALL) return true;
  if (filter === FILTER_NONE) return !document.category;
  return String(document.category?.id) === filter;
}

/** Chip list for the dashboard filter: All, each category, Uncategorized (with document counts). */
export function buildFilterChips(categories, documents) {
  const chips = [
    { key: FILTER_ALL, label: 'All' },
    ...categories.map((category) => ({ key: String(category.id), label: category.name })),
    { key: FILTER_NONE, label: 'Uncategorized' },
  ];
  return chips.map((chip) => ({
    ...chip,
    count: documents.filter((document) => matchesFilter(document, chip.key)).length,
  }));
}

/** Chip list for choosing a document's category: None plus each category. */
export function buildCategoryChoices(categories) {
  return [
    { key: FILTER_NONE, label: 'None' },
    ...categories.map((category) => ({ key: String(category.id), label: category.name })),
  ];
}
