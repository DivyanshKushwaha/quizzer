import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import { quizApi } from "../api";
import useQuizSocket from "../hooks/useQuizSocket";
import TopBar, { StatusBadge } from "../components/TopBar";

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

export default function Browse() {
  const navigate = useNavigate();
  const [quizzes, setQuizzes] = useState([]);
  const [played, setPlayed] = useState([]);
  const [loading, setLoading] = useState(true);
  const events = useQuizSocket("feed");

  const load = async () => {
    try {
      const [browseRes, attemptsRes] = await Promise.all([
        quizApi.browse(),
        quizApi.myAttempts(),
      ]);
      setQuizzes(browseRes.data);
      setPlayed(attemptsRes.data);
    } catch {
      toast.error("Failed to load quizzes");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);
  useEffect(() => { if (events.feed) load(); }, [events.feed]);

  const quizButton = (q) => {
    if (!q.registered) {
      return (
        <button onClick={() => navigate(`/quizzes/${q.id}/lobby`)} className="btn-primary w-full mt-4">
          Enter the Lobby
        </button>
      );
    }
    if (q.status === "live") {
      return (
        <button onClick={() => navigate(`/quizzes/${q.id}/play`)} className="btn-success w-full mt-4">
          Join now
        </button>
      );
    }
    return (
      <button disabled className="btn-primary w-full mt-4 opacity-50 cursor-not-allowed">
        Wait to Join
      </button>
    );
  };

  return (
    <div className="page-bg">
      <TopBar />
      <main className="max-w-6xl mx-auto px-4 py-10 space-y-12">
        <section>
          <h1 className="section-title">Upcoming & Live Quizzes</h1>
          <p className="section-sub mb-8">Register for a quiz and compete live with other players.</p>

          {loading ? (
            <p className="text-slate-500">Loading...</p>
          ) : quizzes.length === 0 ? (
            <div className="text-center py-16 text-slate-500 border border-dashed border-slate-300 rounded-2xl bg-white/60">
              No quizzes available yet. Check back soon.
            </div>
          ) : (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {quizzes.map((q) => (
                <div key={q.id} className="card-hover p-5 flex flex-col animate-float-up">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h3 className="font-bold text-lg text-slate-900 leading-tight">{q.title}</h3>
                    <StatusBadge status={q.status} />
                  </div>
                  <p className="text-sm text-slate-500 flex-1 line-clamp-3">{q.description || "No description."}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <TimePill label="Start" value={q.started_at} color="emerald" />
                    <TimePill label="End" value={q.ends_at} color="rose" />
                  </div>
                  {q.prize?.top3 && (
                    <p className="mt-3 text-xs font-medium text-amber-700 bg-amber-50 border border-amber-100 rounded-lg px-2 py-1 inline-block w-fit">
                      Prize: {q.prize.top3}
                    </p>
                  )}
                  {quizButton(q)}
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="border-t border-slate-200 pt-10">
          <h2 className="section-title">Quizzes You've Played</h2>
          <p className="section-sub mb-8">Your completed attempts and scores.</p>

          {played.length === 0 ? (
            <div className="text-center py-16 text-slate-500 border border-dashed border-slate-300 rounded-2xl bg-white/60">
              You haven't finished any quizzes yet.
            </div>
          ) : (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {played.map((a) => (
                <div key={a.quiz_id} className="card p-5 flex flex-col">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h3 className="font-bold text-lg text-slate-900 leading-tight">{a.title}</h3>
                    <StatusBadge status="finished" />
                  </div>
                  <div className="mt-1 flex flex-wrap gap-2">
                    <TimePill label="Score" value={a.score} color="emerald" />
                    <TimePill label="Time" value={`${Math.round((a.total_time_ms || 0) / 1000)}s`} color="slate" />
                    <TimePill label="Ended" value={a.finished_at} color="rose" />
                  </div>
                  <button onClick={() => navigate(`/quizzes/${a.quiz_id}/result`)} className="btn-secondary w-full mt-4">
                    View result
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
