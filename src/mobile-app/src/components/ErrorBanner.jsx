import { StyleSheet, Text, View } from 'react-native';
import { colors, radius, spacing } from '../theme';

/** Renders nothing when there is no message, so screens can always include it. */
export default function ErrorBanner({ message }) {
  if (!message) return null;

  return (
    <View style={styles.banner} accessibilityRole="alert">
      <Text style={styles.text}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    backgroundColor: colors.dangerBackground,
    borderRadius: radius.md,
    padding: spacing.md,
  },
  text: { color: colors.danger, fontSize: 14 },
});
