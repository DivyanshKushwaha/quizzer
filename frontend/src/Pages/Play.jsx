import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import { quizApi } from "../api";
import { useAuth } from "../context/AuthContext";
import useQuizSocket from "../hooks/useQuizSocket";
import TopBar from "../components/TopBar";
import Timer from "../components/Timer";
import Leaderboard from "../components/Leaderboard";
import SidePanel from "../components/SidePanel";

export default function Play() {
  const { quizId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const events = useQuizSocket(quizId);
  const [state, setState] = useState(null);
  const [selected, setSelected] = useState(null);
  const [busy, setBusy] = useState(false);
  const questionStart = useRef(Date.now());
  const selectedRef = useRef(null);

  const applyState = (data) => {
    if (data.quiz_status === "finished") { navigate(`/quizzes/${quizId}/result`); return; }
    setState(data);
    setSelected(null);
    selectedRef.current = null;
    questionStart.current = Date.now();
  };

  const load = async () => {
    try {
      const { data } = await quizApi.join(quizId);
      applyState(data);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not load quiz");
      navigate("/quizzes");
    }
  };

  useEffect(() => { load(); }, [quizId]);
  useEffect(() => { if (events.finished) navigate(`/quizzes/${quizId}/result`); }, [events.finished]);

  const pick = (i) => {
    if (busy) return;
    setSelected(i);
    selectedRef.current = i;
  };

  const submit = async (idx) => {
    if (busy) return;
    setBusy(true);
    const timeMs = Date.now() - questionStart.current;
    try {
      const { data } = await quizApi.answer(quizId, idx, timeMs);
      applyState(data);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Answer rejected");
      load();
    } finally {
      setBusy(false);
    }
  };

  // Manual advance (Next / Final Submit). On timer expiry, auto-close with whatever is picked (or skip).
  const advance = () => submit(selectedRef.current == null ? -1 : selectedRef.current);

  if (!state) return <div className="page-bg"><TopBar /><p className="p-8 text-slate-500">Loading quiz...</p></div>;

  const q = state.question;
  const submitted = state.status === "finished";
  const isLast = state.question_index + 1 >= state.total_questions;
  const progress = (state.question_index / state.total_questions) * 100;

  return (
    <div className="page-bg">
      <TopBar />
      <main className="max-w-6xl mx-auto px-4 py-8 grid lg:grid-cols-3 gap-6">
        <section className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Question {state.question_index + 1} of {state.total_questions}</p>
              <div className="mt-2 w-52 h-2 rounded-full bg-slate-200 overflow-hidden">
                <div className="h-full bg-indigo-500 transition-all rounded-full" style={{ width: `${progress}%` }} />
              </div>
            </div>
            <div className="flex items-center gap-6">
              {state.quiz_ends_at && (
                <Timer deadline={state.quiz_ends_at} label="Overall" onExpire={() => navigate(`/quizzes/${quizId}/result`)} />
              )}
              <div className="text-right card px-4 py-2">
                <div className="text-[10px] uppercase tracking-wide text-slate-500">Score</div>
                <div className="text-2xl font-extrabold text-indigo-600 tabular-nums">{state.score}</div>
              </div>
            </div>
          </div>

          {submitted ? (
            <div className="card p-10 text-center animate-pop-in shadow-md">
              <div className="w-14 h-14 mx-auto mb-4 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center">
                <svg className="w-7 h-7 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-slate-900">Answers submitted!</h2>
              <p className="text-slate-500 mt-1">Results are announced when the quiz ends. Hang tight — the leaderboard keeps updating live.</p>
            </div>
          ) : q ? (
            <div key={q.index} className="card p-6 animate-pop-in shadow-md">
              <div className="flex items-start justify-between gap-4 mb-5">
                <h2 className="text-xl font-bold text-slate-900 leading-snug">{q.text}</h2>
                {state.question_deadline && (
                  <div className="shrink-0 w-16 h-16 rounded-full border-2 border-indigo-200 bg-indigo-50 flex items-center justify-center">
                    <Timer deadline={state.question_deadline} onExpire={advance} />
                  </div>
                )}
              </div>
              <div className="grid sm:grid-cols-2 gap-3">
                {q.options.map((opt, i) => (
                  <button key={i} disabled={busy} onClick={() => pick(i)}
                    className={`text-left px-4 py-3.5 rounded-xl border text-sm font-medium transition ${
                      selected === i
                        ? "bg-indigo-600 border-indigo-600 text-white shadow-md shadow-indigo-200"
                        : "bg-white border-slate-200 text-slate-800 hover:border-indigo-300 hover:bg-indigo-50/50"
                    } disabled:cursor-not-allowed`}>
                    <span className={`mr-2 font-bold ${selected === i ? "text-indigo-200" : "text-indigo-500"}`}>
                      {String.fromCharCode(65 + i)}.
                    </span>
                    {opt}
                  </button>
                ))}
              </div>
              <div className="mt-5 flex items-center justify-between gap-4">
                <p className="text-xs text-slate-400">Score updates live. Correctness is revealed only at the end.</p>
                <button
                  onClick={advance}
                  disabled={busy || selected === null}
                  className={`${isLast ? "btn-success" : "btn-primary"} px-6 disabled:opacity-50 disabled:cursor-not-allowed`}>
                  {isLast ? "Final Submit" : "Next"}
                </button>
              </div>
            </div>
          ) : (
            <div className="card p-10 text-center text-slate-500">Waiting for the next question...</div>
          )}
        </section>

        <aside className="space-y-5">
          <SidePanel quizId={quizId} events={events} />
          <Leaderboard quizId={quizId} myId={user?.id} events={events} />
        </aside>
      </main>
    </div>
  );
}
