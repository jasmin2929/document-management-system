export function formatFileSize(bytes) {
  if (bytes === null || bytes === undefined) return '—';
  if (bytes < 1024) return `${bytes} B`;
  const units = ['KB', 'MB', 'GB'];
  let value = bytes / 1024;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(1)} ${units[unitIndex]}`;
}

// Mon MM, YYYY, HH:MM AM/PM withSeconds adds ":SS"
export function formatDate(isoString, { withSeconds = false } = {}) {
  if (!isoString) return '—';
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return '—';
  const day = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  const time = date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    ...(withSeconds && { second: '2-digit' }),
  });
  return `${day}, ${time}`;
}

export function formatStatus(status) {
  if (!status) return 'Unknown';
  return status.charAt(0) + status.slice(1).toLowerCase();
}
