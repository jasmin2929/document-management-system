// Central design tokens, so screens and components stay consistent

export const colors = {
  background: '#f5f6f8',
  surface: '#ffffff',
  border: '#e2e5ea',
  text: '#1d2330',
  muted: '#6b7280',
  primary: '#2563eb',
  onPrimary: '#ffffff',
  danger: '#dc2626',
  dangerBackground: '#fdecec',
  status: {
    pending: '#b45309',
    processing: '#2563eb',
    processed: '#15803d',
    failed: '#dc2626',
  },
};

export const spacing = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24 };

export const radius = { sm: 6, md: 10, pill: 999 };

export const typography = {
  title: { fontSize: 20, fontWeight: '700', color: colors.text },
  body: { fontSize: 15, color: colors.text },
  label: { fontSize: 13, fontWeight: '600', color: colors.muted },
  small: { fontSize: 13, color: colors.muted },
};
