import { formatStatus } from '../utils/format';

export default function StatusBadge({ status }) {
  const modifier = (status || 'pending').toLowerCase();
  return (
    <span className={`status status--${modifier}`}>
      <span className="status__dot" aria-hidden="true" />
      {formatStatus(status)}
    </span>
  );
}
