import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children, role }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="page-bg flex items-center justify-center text-slate-500">Loading...</div>;
  }
  if (!user) return <Navigate to="/login" replace />;
  if (role && user.role !== role) {
    return <div className="page-bg flex items-center justify-center text-slate-500">Not authorized for this page.</div>;
  }
  return children;
}
