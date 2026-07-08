import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import { authApi } from "../api";
import { useAuth } from "../context/AuthContext";
import AuthShell, { inputClass, btnClass } from "../components/AuthShell";

const empty = {
  first_name: "",
  last_name: "",
  username: "",
  email: "",
  password: "",
  role: "player",
};

export default function Register() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState(empty);
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await authApi.register(form);
      const u = await login(form.email, form.password);
      toast.success("Account created!");
      navigate(u?.role === "admin" ? "/admin" : "/quizzes");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Registration failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell title="Create account" subtitle="Join as a player or quiz organizer">
      <form onSubmit={submit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <input className={inputClass} placeholder="First name" value={form.first_name} onChange={set("first_name")} required />
          <input className={inputClass} placeholder="Last name" value={form.last_name} onChange={set("last_name")} required />
        </div>
        <input className={inputClass} placeholder="Username" value={form.username} onChange={set("username")} required />
        <input className={inputClass} type="email" placeholder="Email" value={form.email} onChange={set("email")} required />
        <input className={inputClass} type="password" placeholder="Password" value={form.password} onChange={set("password")} required />

        <div className="grid grid-cols-2 gap-3">
          {["player", "admin"].map((r) => (
            <button type="button" key={r} onClick={() => setForm({ ...form, role: r })}
              className={`py-2.5 rounded-xl text-sm font-semibold capitalize border transition ${
                form.role === r
                  ? "bg-indigo-600 border-indigo-600 text-white shadow-sm"
                  : "bg-white border-slate-200 text-slate-600 hover:border-indigo-200"
              }`}>
              {r === "admin" ? "Quiz Organizer" : "Player"}
            </button>
          ))}
        </div>

        <button className={btnClass} disabled={busy}>
          {busy ? "Creating..." : "Create account"}
        </button>
      </form>
      <p className="text-center text-sm text-slate-500 mt-4">
        Already have an account?{" "}
        <Link to="/login" className="text-indigo-600 font-medium hover:underline">Sign in</Link>
      </p>
    </AuthShell>
  );
}
