import { ActivityIndicator, Pressable, StyleSheet, Text } from 'react-native';
import { colors, radius, spacing } from '../theme';

/**
 * @param variant 'primary' | 'secondary' | 'danger'
 * @param loading shows a spinner and disables the button
 */
export default function Button({ title, onPress, variant = 'primary', disabled = false, loading = false, style }) {
  const isDisabled = disabled || loading;
  const textColor = variant === 'primary' ? colors.onPrimary : variant === 'danger' ? colors.danger : colors.text;

  return (
    <Pressable
      onPress={onPress}
      disabled={isDisabled}
      accessibilityRole="button"
      accessibilityLabel={title}
      accessibilityState={{ disabled: isDisabled, busy: loading }}
      style={({ pressed }) => [
        styles.base,
        styles[variant],
        pressed && styles.pressed,
        isDisabled && styles.disabled,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={textColor} />
      ) : (
        <Text style={[styles.text, { color: textColor }]}>{title}</Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    minHeight: 44, // Apple's minimum touch target
    paddingHorizontal: spacing.lg,
    borderRadius: radius.md,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
  },
  primary: { backgroundColor: colors.primary, borderColor: colors.primary },
  secondary: { backgroundColor: colors.surface, borderColor: colors.border },
  danger: { backgroundColor: colors.dangerBackground, borderColor: colors.dangerBackground },
  pressed: { opacity: 0.75 },
  disabled: { opacity: 0.5 },
  text: { fontSize: 15, fontWeight: '600' },
});
