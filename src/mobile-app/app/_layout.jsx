import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { colors } from '../src/theme';

// Navigation: Documents (list) -> Document (detail); Upload opens as an iOS modal sheet
export default function RootLayout() {
  return (
    <>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerTintColor: colors.primary,
          headerTitleStyle: { color: colors.text },
          contentStyle: { backgroundColor: colors.background },
        }}
      >
        <Stack.Screen name="index" options={{ title: 'Documents', headerLargeTitle: true }} />
        <Stack.Screen name="documents/[id]" options={{ title: 'Document' }} />
        <Stack.Screen name="upload" options={{ title: 'Upload document', presentation: 'modal' }} />
      </Stack>
    </>
  );
}
