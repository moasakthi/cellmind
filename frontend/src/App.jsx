import { Navigate, Route, Routes } from "react-router-dom";
import RequireAuth from "./auth/RequireAuth.jsx";
import ProtectedShell from "./components/ProtectedShell.jsx";
import Landing from "./pages/Landing.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Investigation from "./pages/Investigation.jsx";
import Recommendation from "./pages/Recommendation.jsx";
import Inference from "./pages/Inference.jsx";
import Cameras from "./pages/Cameras.jsx";
import Retraining from "./pages/Retraining.jsx";
import Taxonomy from "./pages/Taxonomy.jsx";
import Rbac from "./pages/Rbac.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />

      <Route
        path="/app"
        element={
          <RequireAuth>
            <ProtectedShell />
          </RequireAuth>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="inference" element={<Inference />} />
        <Route path="investigation" element={<Investigation />} />
        <Route path="recommendation" element={<Recommendation />} />
        <Route path="cameras" element={<Cameras />} />
        <Route path="retraining" element={<Retraining />} />
        <Route path="taxonomy" element={<Taxonomy />} />
        <Route path="rbac" element={<Rbac />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
