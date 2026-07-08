import { useEffect, useState } from "react";
import { quizApi } from "../api";

export default function SidePanel({ quizId, events }) {
  const [data, setData] = useState({ playing: 0, finished: 0, players: [] });

  const load = async () => {
    try {
      const { data } = await quizApi.presence(quizId);
      setData(data);
    } catch { /* ignore */ }
  };

  useEffect(() => { load(); }, [quizId, events?.presence]);

  const groups = {};
  data.players?.forEach((p) => {
    const q = p.question_index + 1;
    groups[q] = (groups[q] || 0) + 1;
  });

  return (
    <div className="card p-4">
      <h3 className="font-semibold text-sm text-slate-800 mb-3">Live Activity</h3>
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="rounded-xl bg-emerald-50 border border-emerald-100 p-3 text-center">
          <div className="text-2xl font-bold text-emerald-600">{data.playing}</div>
          <div className="text-[11px] text-slate-500">Playing now</div>
        </div>
        <div className="rounded-xl bg-slate-50 border border-slate-200 p-3 text-center">
          <div className="text-2xl font-bold text-slate-700">{data.finished}</div>
          <div className="text-[11px] text-slate-500">Completed</div>
        </div>
      </div>
      <h4 className="text-xs font-semibold text-slate-500 mb-2">Progress</h4>
      <div className="space-y-1.5">
        {Object.keys(groups).length === 0 && <p className="text-xs text-slate-400">No active players.</p>}
        {Object.entries(groups).sort((a, b) => a[0] - b[0]).map(([q, count]) => (
          <div key={q} className="flex items-center gap-2 text-xs">
            <span className="text-slate-500 w-14 font-medium">Q{q}</span>
            <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
              <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${Math.min(100, count * 20)}%` }} />
            </div>
            <span className="text-slate-600 w-6 text-right font-medium">{count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
