import { Link, Outlet } from 'react-router-dom';

export default function Layout() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/" className="app-header__brand">
          <span className="app-header__logo" aria-hidden="true" />
          Documents
        </Link>
      </header>
      <Outlet />
    </div>
  );
}
