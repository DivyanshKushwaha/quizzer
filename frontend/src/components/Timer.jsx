import { useEffect, useState } from "react";

// Counts down from `seconds` (per-question) or to an ISO deadline (overall).
export default function Timer({ seconds, deadline, onExpire, label }) {
  const compute = () => {
    if (deadline) return Math.max(0, Math.round((new Date(deadline) - Date.now()) / 1000));
    return seconds ?? 0;
  };
  const [remaining, setRemaining] = useState(compute);

  useEffect(() => {
    setRemaining(compute());
    const t = setInterval(() => {
      setRemaining((r) => {
        const next = deadline ? compute() : r - 1;
        if (next <= 0) {
          clearInterval(t);
          onExpire?.();
          return 0;
        }
        return next;
      });
    }, 1000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seconds, deadline]);

  const mins = Math.floor(remaining / 60);
  const secs = remaining % 60;
  const danger = remaining <= 5;

  return (
    <div className="flex flex-col items-center">
      {label && <span className="text-[10px] uppercase tracking-wide text-slate-500 font-medium">{label}</span>}
      <span className={`font-mono font-bold tabular-nums ${danger ? "text-red-500" : "text-slate-800"}`}>
        {mins > 0 ? `${mins}:${String(secs).padStart(2, "0")}` : `${secs}s`}
      </span>
    </div>
  );
}
