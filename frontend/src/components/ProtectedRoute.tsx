import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

/**
 * Se non autenticato, reindirizza a /login preservando il percorso di
 * provenienza (così dopo il login si può tornare dove l'utente voleva
 * andare). Le route figlie vengono renderizzate tramite <Outlet />.
 */
export function ProtectedRoute() {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  return <Outlet />;
}
