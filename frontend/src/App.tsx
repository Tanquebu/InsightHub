import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { DatasetDetailPage } from "./pages/DatasetDetailPage";
import { LoginPage } from "./pages/LoginPage";
import { ProjectsDatasetsPage } from "./pages/ProjectsDatasetsPage";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/" element={<Navigate to="/datasets" replace />} />
            <Route path="/datasets" element={<ProjectsDatasetsPage />} />
            <Route
              path="/projects/:projectId/datasets/:datasetId"
              element={<DatasetDetailPage />}
            />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
