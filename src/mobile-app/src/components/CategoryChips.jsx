import { Pressable, ScrollView, StyleSheet, Text } from 'react-native';
import { colors, radius, spacing } from '../theme';

/**
 * Horizontally scrollable single-choice chips (used for the dashboard filter and the category choice).
 * @param chips [{ key, label, count? }]
 */
export default function CategoryChips({ chips, selectedKey, onSelect, disabled = false }) {
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      keyboardShouldPersistTaps="handled"
      contentContainerStyle={styles.row}
    >
      {chips.map((chip) => {
        const active = chip.key === selectedKey;
        return (
          <Pressable
            key={chip.key}
            onPress={() => onSelect(chip.key)}
            disabled={disabled}
            accessibilityRole="button"
            accessibilityLabel={chip.count === undefined ? chip.label : `${chip.label}, ${chip.count} documents`}
            accessibilityState={{ selected: active, disabled }}
            style={({ pressed }) => [
              styles.chip,
              active && styles.chipActive,
              pressed && styles.pressed,
              disabled && styles.disabled,
            ]}
          >
            <Text style={[styles.label, active && styles.labelActive]}>{chip.label}</Text>
            {chip.count !== undefined && (
              <Text style={[styles.count, active && styles.labelActive]}>{chip.count}</Text>
            )}
          </Pressable>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  row: { gap: spacing.sm, paddingVertical: spacing.xs },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    minHeight: 36,
    paddingHorizontal: spacing.md,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  chipActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  pressed: { opacity: 0.75 },
  disabled: { opacity: 0.5 },
  label: { fontSize: 14, fontWeight: '500', color: colors.text },
  labelActive: { color: colors.onPrimary },
  count: { fontSize: 12, color: colors.muted },
});
