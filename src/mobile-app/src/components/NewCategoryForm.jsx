import { useState } from 'react';
import { StyleSheet, Text, TextInput, View } from 'react-native';
import { createCategory } from '../api/categories';
import { colors, radius, spacing } from '../theme';
import { validateCategoryName } from '../utils/validation';
import Button from './Button';

export default function NewCategoryForm({ onCreated }) {
  const [name, setName] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    const validationError = validateCategoryName(name);
    setError(validationError);
    if (validationError) return;

    setSubmitting(true);
    try {
      await createCategory(name.trim());
      setName('');
      onCreated();
    } catch (err) {
      // e.g. 409 "The request was not completed because the value you entered already exists."
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <View style={styles.container}>
      <View style={styles.row}>
        <TextInput
          style={[styles.input, error && styles.inputInvalid]}
          value={name}
          onChangeText={(text) => {
            setName(text);
            setError(null);
          }}
          onSubmitEditing={handleSubmit}
          placeholder="New category"
          placeholderTextColor={colors.muted}
          returnKeyType="done"
          accessibilityLabel="New category name"
        />
        <Button title="Add" variant="secondary" onPress={handleSubmit} loading={submitting} />
      </View>
      {error && (
        <Text style={styles.error} accessibilityRole="alert">
          {error}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: spacing.xs },
  row: { flexDirection: 'row', gap: spacing.sm },
  input: {
    flex: 1,
    minHeight: 44,
    paddingHorizontal: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    fontSize: 15,
    color: colors.text,
  },
  inputInvalid: { borderColor: colors.danger },
  error: { color: colors.danger, fontSize: 13 },
});
