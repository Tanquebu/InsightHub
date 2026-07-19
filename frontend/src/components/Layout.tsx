import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function Layout() {
  const { logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/datasets" className="app-title">
          InsightHub
        </Link>
        <button type="button" className="btn btn-link" onClick={logout}>
          Esci
        </button>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
