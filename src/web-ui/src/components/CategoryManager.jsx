import { useState } from 'react';
import { createCategory } from '../api/categories';
import { validateCategoryName } from '../utils/validation';

export default function CategoryManager({ categories, selectedCategoryId, onSelectCategory, onCategoryCreated }) {
  const [newName, setNewName] = useState('');
  const [fieldError, setFieldError] = useState(null);
  const [submitError, setSubmitError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleCreate(event) {
    event.preventDefault();
    setSubmitError(null);

    const errors = validateCategoryName(newName);
    setFieldError(errors.name || null);
    if (errors.name) {
      return;
    }

    setSubmitting(true);
    try {
      await createCategory(newName.trim());
      setNewName('');
      onCategoryCreated();
    } catch (error) {
      setSubmitError(error.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <label htmlFor="category-filter">Filter by category</label>
      <br />
      <select
        id="category-filter"
        value={selectedCategoryId}
        onChange={(event) => onSelectCategory(event.target.value)}
      >
        <option value="">All categories</option>
        {categories.map((category) => (
          <option key={category.id} value={category.id}>
            {category.name}
          </option>
        ))}
      </select>

      <form onSubmit={handleCreate} noValidate>
        <label htmlFor="new-category">New category</label>
        <br />
        <input
          id="new-category"
          type="text"
          value={newName}
          onChange={(event) => setNewName(event.target.value)}
          placeholder="Category name"
        />
        <button type="submit" disabled={submitting}>
          Add
        </button>
        {fieldError && <div role="alert">{fieldError}</div>}
        {submitError && <div role="alert">{submitError}</div>}
      </form>
    </div>
  );
}
