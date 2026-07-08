import { useEffect, useState } from "react";
import { quizApi } from "../api";

export default function Leaderboard({ quizId, myId, events }) {
  const [view, setView] = useState("me");
  const [rows, setRows] = useState([]);

  const load = async () => {
    try {
      const { data } = view === "top"
        ? await quizApi.leaderboardTop(quizId)
        : await quizApi.leaderboard(quizId);
      setRows(data);
    } catch { /* ignore */ }
  };

  useEffect(() => { load(); }, [quizId, view, events?.leaderboard]);

  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-sm text-slate-800">Leaderboard</h3>
        <div className="flex text-xs rounded-lg overflow-hidden border border-slate-200 bg-slate-50">
          <button onClick={() => setView("me")}
            className={`px-2.5 py-1 ${view === "me" ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-white"}`}>
            Around me
          </button>
          <button onClick={() => setView("top")}
            className={`px-2.5 py-1 ${view === "top" ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-white"}`}>
            Top 10
          </button>
        </div>
      </div>
      <div className="space-y-1.5 max-h-[420px] overflow-y-auto no-scrollbar">
        {rows.length === 0 && <p className="text-xs text-slate-400 py-4 text-center">No scores yet.</p>}
        {rows.map((r) => {
          const mine = r.player_id === myId;
          return (
            <div key={r.player_id}
              className={`flex items-center gap-3 px-3 py-2 rounded-xl text-sm ${
                mine ? "bg-indigo-50 border border-indigo-200" : "bg-slate-50 border border-transparent"
              }`}>
              <span className="w-6 text-center font-bold text-slate-400">{r.rank}</span>
              <span className="flex-1 truncate text-slate-700">
                {r.display_name} {mine && <span className="text-indigo-600 font-medium">(you)</span>}
              </span>
              <span className="font-mono font-semibold text-slate-900">{r.score ?? ""}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
