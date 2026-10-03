import { useState } from 'react';
import { createCategory } from '../api/categories';
import { FILTER_ALL, FILTER_NONE, matchesFilter } from '../utils/filters';
import { validateCategoryName } from '../utils/validation';

export default function CategoryBar({ categories, documents, filter, onFilterChange, onCategoryCreated }) {
  const [newName, setNewName] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const chips = [
    { key: FILTER_ALL, name: 'All' },
    ...categories.map((category) => ({ key: String(category.id), name: category.name })),
    { key: FILTER_NONE, name: 'Uncategorized' },
  ];

  async function handleSubmit(event) {
    event.preventDefault();

    const errors = validateCategoryName(newName);
    setError(errors.name || null);
    if (errors.name) return;

    setSubmitting(true);
    try {
      await createCategory(newName.trim());
      setNewName('');
      onCategoryCreated();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="category-bar">
      <div className="chips" role="group" aria-label="Filter by category">
        {chips.map((chip) => {
          const active = filter === chip.key;
          const count = documents.filter((document) => matchesFilter(document, chip.key)).length;
          return (
            <button
              key={chip.key}
              type="button"
              className={`chip${active ? ' chip--active' : ''}`}
              aria-pressed={active}
              onClick={() => onFilterChange(chip.key)}
            >
              {chip.name}
              <span className="chip__count">{count}</span>
            </button>
          );
        })}
      </div>

      <form className="category-form" onSubmit={handleSubmit} noValidate>
        <div className="category-form__row">
          <input
            className={`input input--sm${error ? ' input--invalid' : ''}`}
            value={newName}
            onChange={(event) => {
              setNewName(event.target.value);
              setError(null);
            }}
            placeholder="New category"
            aria-label="New category name"
            aria-invalid={Boolean(error)}
          />
          <button type="submit" className="btn btn--secondary btn--sm" disabled={submitting}>
            Add
          </button>
        </div>
        {error && (
          <div className="field-error" role="alert">
            {error}
          </div>
        )}
      </form>
    </div>
  );
}
