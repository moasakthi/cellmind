import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext.jsx";

export default function RequireAuth({ children }) {
  const { session } = useAuth();
  const location = useLocation();
  if (!session) return <Navigate to="/login" state={{ from: location }} replace />;
  return children;
}
