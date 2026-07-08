import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function TopBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const home = user?.role === "admin" ? "/admin" : "/quizzes";

  return (
    <header className="sticky top-0 z-20 bg-white/90 backdrop-blur border-b border-slate-200/80 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to={home} className="font-extrabold tracking-tight text-slate-900">
          Quiz<span className="text-indigo-600">Arena</span>
        </Link>
        <div className="flex items-center gap-3 text-sm">
          {user && (
            <span className="px-2.5 py-1 rounded-full bg-indigo-50 border border-indigo-100 capitalize text-indigo-700 font-medium">
              {user.role}
            </span>
          )}
          <button onClick={async () => { await logout(); navigate("/login"); }} className="btn-secondary py-1.5">
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}

export function StatusBadge({ status }) {
  const map = {
    live: "bg-emerald-50 text-emerald-700 border-emerald-200",
    lobby: "bg-amber-50 text-amber-700 border-amber-200",
    finished: "bg-slate-100 text-slate-600 border-slate-200",
    draft: "bg-indigo-50 text-indigo-700 border-indigo-200",
  };
  const label = status === "draft" ? "upcoming" : status;
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border capitalize ${map[status] || map.draft}`}>
      {label}
    </span>
  );
}
