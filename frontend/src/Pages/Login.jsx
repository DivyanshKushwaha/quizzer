import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import { useAuth } from "../context/AuthContext";
import { inputClass, btnClass } from "../components/AuthShell";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const u = await login(form.email, form.password);
      toast.success("Welcome back!");
      navigate(u?.role === "admin" ? "/admin" : "/quizzes");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Login failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      <div className="hidden lg:flex flex-col justify-center px-12 bg-gradient-to-br from-indigo-600 via-indigo-500 to-violet-600 text-white">
        <div className="max-w-md animate-float-up">
          <div className="text-5xl mb-6">⚡</div>
          <h1 className="text-4xl font-extrabold leading-tight">QuizArena</h1>
          <p className="mt-4 text-indigo-100 text-lg leading-relaxed">
            Live multiplayer quizzes. Compete in real time, climb the leaderboard, and win prizes.
          </p>
          <ul className="mt-8 space-y-3 text-sm text-indigo-100/90">
            <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-white" /> Real-time scoring & rankings</li>
            <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-white" /> Server-enforced timers</li>
            <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-white" /> Admin & player roles</li>
          </ul>
        </div>
      </div>

      <div className="flex items-center justify-center px-4 py-10 bg-gradient-to-b from-slate-50 to-white">
        <div className="w-full max-w-md animate-pop-in">
          <div className="lg:hidden text-center mb-6">
            <div className="text-3xl mb-2">⚡</div>
            <div className="text-xl font-extrabold text-slate-900">QuizArena</div>
          </div>
          <div className="card p-8 shadow-lg shadow-slate-200/60">
            <h2 className="text-xl font-bold text-slate-900">Sign in</h2>
            <p className="text-sm text-slate-500 mt-1 mb-6">Enter your account to continue</p>
            <form onSubmit={submit} className="space-y-4">
              <input className={inputClass} type="email" placeholder="Email" value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })} required />
              <input className={inputClass} type="password" placeholder="Password" value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })} required />
              <button className={btnClass} disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button>
            </form>
            <p className="text-center text-sm text-slate-500 mt-5">
              No account? <Link to="/register" className="text-indigo-600 font-medium hover:underline">Register</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
