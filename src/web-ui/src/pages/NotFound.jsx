import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <main className="page">
      <h1 className="page-title">Page not found</h1>
      <p className="muted">
        <Link to="/">Back to dashboard</Link>
      </p>
    </main>
  );
}
