import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import confetti from "canvas-confetti";
import { quizApi } from "../api";
import TopBar from "../components/TopBar";

const TIERS = {
  top3: {
    title: "Congratulations, you won!",
    sub: "You finished in the top 3.",
    ring: "ring-amber-200",
    bg: "bg-gradient-to-b from-amber-50 to-white",
    accent: "text-amber-600",
    badge: "Top 3",
  },
  top10: {
    title: "You made the top 10!",
    sub: "You've earned a prize.",
    ring: "ring-indigo-200",
    bg: "bg-gradient-to-b from-indigo-50 to-white",
    accent: "text-indigo-600",
    badge: "Top 10",
  },
  rest: {
    title: "Quiz complete",
    sub: "Well played — here's how you finished.",
    ring: "ring-slate-200",
    bg: "bg-gradient-to-b from-slate-50 to-white",
    accent: "text-slate-600",
    badge: "Finished",
  },
};

export default function Result() {
  const { quizId } = useParams();
  const navigate = useNavigate();
  const [res, setRes] = useState(null);
  const [waiting, setWaiting] = useState(false);

  useEffect(() => {
    let active = true;
    let timer = null;

    const fetchResult = async () => {
      try {
        const { data } = await quizApi.result(quizId);
        if (active) setRes(data);
      } catch (err) {
        const status = err?.response?.status;
        if (status === 403 && /announced after/i.test(err?.response?.data?.detail || "")) {
          if (active) { setWaiting(true); timer = setTimeout(fetchResult, 2500); }
        } else if (active) {
          navigate("/quizzes");
        }
      }
    };

    fetchResult();
    return () => { active = false; if (timer) clearTimeout(timer); };
  }, [quizId, navigate]);

  useEffect(() => {
    if (!res) return;
    if (res.tier === "top3") {
      const end = Date.now() + 2500;
      const frame = () => {
        confetti({ particleCount: 5, angle: 60, spread: 55, origin: { x: 0 } });
        confetti({ particleCount: 5, angle: 120, spread: 55, origin: { x: 1 } });
        if (Date.now() < end) requestAnimationFrame(frame);
      };
      frame();
    } else if (res.tier === "top10") {
      confetti({ particleCount: 120, spread: 70, origin: { y: 0.6 } });
    }
  }, [res]);

  if (!res) return (
    <div className="page-bg">
      <TopBar />
      <main className="max-w-lg mx-auto px-4 py-16">
        <div className="card p-10 text-center shadow-md">
          <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-indigo-50 border border-indigo-100 flex items-center justify-center">
            <div className="w-5 h-5 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
          </div>
          <h2 className="text-lg font-bold text-slate-900">
            {waiting ? "Waiting for final results..." : "Loading result..."}
          </h2>
          {waiting && <p className="text-sm text-slate-500 mt-1">Results are announced once the quiz ends.</p>}
        </div>
      </main>
    </div>
  );

  const t = TIERS[res.tier] || TIERS.rest;
  const timeSec = (res.total_time_ms / 1000).toFixed(1);

  return (
    <div className="page-bg">
      <TopBar />
      <main className="max-w-lg mx-auto px-4 py-12">
        <div className={`card p-8 text-center animate-pop-in shadow-lg ring-2 ${t.ring} ${t.bg}`}>
          <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${t.accent} bg-white border border-current mb-4`}>
            {t.badge}
          </span>
          <h1 className="text-2xl font-extrabold text-slate-900">{t.title}</h1>
          <p className="text-slate-500 mt-1">{t.sub}</p>

          <div className="my-8 flex items-center justify-center gap-8">
            <div>
              <div className={`text-4xl font-extrabold ${t.accent}`}>#{res.rank}</div>
              <div className="text-xs text-slate-500 mt-1">Rank</div>
            </div>
            <div className="h-12 w-px bg-slate-200" />
            <div>
              <div className="text-4xl font-extrabold text-slate-900">{res.score}</div>
              <div className="text-xs text-slate-500 mt-1">Score</div>
            </div>
            <div className="h-12 w-px bg-slate-200" />
            <div>
              <div className="text-4xl font-extrabold text-slate-900">{timeSec}s</div>
              <div className="text-xs text-slate-500 mt-1">Total time</div>
            </div>
          </div>

          {res.prize && res.tier !== "rest" && (
            <div className="mb-6 rounded-xl bg-amber-50 border border-amber-200 p-4">
              <div className="text-xs uppercase tracking-wide text-amber-700 mb-1 font-semibold">Your prize</div>
              <div className="font-bold text-amber-900">{res.prize}</div>
            </div>
          )}

          <button onClick={() => navigate("/quizzes")} className="btn-primary w-full">Back to quizzes</button>
        </div>
      </main>
    </div>
  );
}
