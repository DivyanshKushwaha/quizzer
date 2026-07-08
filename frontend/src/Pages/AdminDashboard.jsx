import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import { adminApi, quizApi } from "../api";
import useQuizSocket from "../hooks/useQuizSocket";
import TopBar, { StatusBadge } from "../components/TopBar";

const MEDALS = ["🥇", "🥈", "🥉"];

const PILL_COLORS = {
  slate: "bg-slate-100 text-slate-600 border-slate-200",
  emerald: "bg-emerald-50 text-emerald-700 border-emerald-200",
  rose: "bg-rose-50 text-rose-700 border-rose-200",
};

function TimePill({ label, value, color = "slate" }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${PILL_COLORS[color]}`}>
      <span className="opacity-70">{label}</span>
      <span className="font-semibold">{value}</span>
    </span>
  );
}

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [quizzes, setQuizzes] = useState([]);
  const [tops, setTops] = useState({});
  const [loading, setLoading] = useState(true);
  const events = useQuizSocket("feed");

  const load = async () => {
    try {
      const { data } = await adminApi.list();
      setQuizzes(data);
      const ranked = data.filter((q) => q.status === "live" || q.status === "finished");
      const results = await Promise.all(
        ranked.map((q) =>
          quizApi.leaderboardTop(q.id).then(({ data }) => [q.id, data.slice(0, 3)]).catch(() => [q.id, []])
        )
      );
      setTops(Object.fromEntries(results));
    } catch {
      toast.error("Failed to load your quizzes");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);
  useEffect(() => { if (events.feed) load(); }, [events.feed]);

  const start = async (id) => {
    try {
      await adminApi.start(id);
      toast.success("Quiz is live!");
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not start quiz");
    }
  };

  const remove = async (id) => {
    if (!confirm("Delete this quiz? This cannot be undone.")) return;
    try {
      await adminApi.remove(id);
      toast.success("Quiz deleted");
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not delete quiz");
    }
  };

  return (
    <div className="page-bg">
      <TopBar />
      <main className="max-w-6xl mx-auto px-4 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="section-title">Your Quizzes</h1>
            <p className="section-sub">Create, manage, and launch live quizzes.</p>
          </div>
          <Link to="/admin/quizzes/new" className="btn-primary">+ New quiz</Link>
        </div>

        {loading ? (
          <p className="text-slate-500">Loading...</p>
        ) : quizzes.length === 0 ? (
          <div className="text-center py-20 text-slate-500 border border-dashed border-slate-300 rounded-2xl bg-white/60">
            No quizzes yet. Click <span className="text-indigo-600 font-medium">New quiz</span> to build your first one.
          </div>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-2">
            {quizzes.map((q) => {
              const draft = q.status === "draft" || q.status === "lobby";
              return (
                <div key={q.id} className="card-hover p-7 flex flex-col min-h-[16rem] animate-float-up">
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <h3 className="font-bold text-xl text-slate-900 leading-tight">{q.title}</h3>
                    <StatusBadge status={q.status} />
                  </div>
                  <p className="text-sm text-slate-500 flex-1 line-clamp-3 leading-relaxed">{q.description || "No description."}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <TimePill label="Created" value={q.created_at} color="slate" />
                    <TimePill label="Start" value={q.started_at} color="emerald" />
                    <TimePill label="End" value={q.ends_at} color="rose" />
                  </div>
                  {(q.status === "live" || q.status === "finished") && (
                    <div className="mt-4">
                      <p className="text-xs font-semibold text-slate-500 mb-2">Top 3 players</p>
                      {(tops[q.id]?.length ?? 0) === 0 ? (
                        <p className="text-xs text-slate-400">No scores yet.</p>
                      ) : (
                        <ol className="space-y-1">
                          {tops[q.id].map((p, i) => (
                            <li key={p.player_id} className="flex items-center gap-2 text-sm">
                              <span className="w-5 text-center">{MEDALS[i] || i + 1}</span>
                              <span className="flex-1 truncate text-slate-700">{p.display_name}</span>
                              <span className="font-mono font-semibold text-slate-900">{p.score ?? 0}</span>
                            </li>
                          ))}
                        </ol>
                      )}
                    </div>
                  )}
                  <div className="mt-5 pt-4 border-t border-slate-100 flex flex-wrap gap-2">
                    {draft && (
                      <>
                        <button onClick={() => navigate(`/admin/quizzes/${q.id}`)} className="btn-secondary text-sm py-1.5">Edit</button>
                        <button onClick={() => start(q.id)} className="btn-success text-sm py-1.5">Start</button>
                        <button onClick={() => remove(q.id)} className="text-sm py-1.5 px-3 rounded-xl bg-red-50 border border-red-200 text-red-600 hover:bg-red-100 transition">Delete</button>
                      </>
                    )}
                    {q.status === "live" && (
                      <span className="text-sm text-emerald-600 font-medium flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" /> Running live
                      </span>
                    )}
                    {q.status === "finished" && <span className="text-sm text-slate-400">Finished</span>}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
