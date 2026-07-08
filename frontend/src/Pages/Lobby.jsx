import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import { quizApi } from "../api";
import useQuizSocket from "../hooks/useQuizSocket";
import TopBar, { StatusBadge } from "../components/TopBar";

export default function Lobby() {
  const { quizId } = useParams();
  const navigate = useNavigate();
  const [quiz, setQuiz] = useState(null);
  const [registered, setRegistered] = useState([]);
  const [displayName, setDisplayName] = useState("");
  const [joined, setJoined] = useState(false);
  const events = useQuizSocket(quizId);

  const load = async () => {
    try {
      const { data } = await quizApi.lobby(quizId);
      setQuiz(data.quiz);
      setRegistered(data.registered);
      if (data.is_registered) setJoined(true);
    } catch {
      toast.error("Failed to load lobby");
    }
  };

  useEffect(() => { load(); }, [quizId]);
  useEffect(() => { if (events.lobby || events.started) load(); }, [events.lobby, events.started]);

  const register = async () => {
    try {
      await quizApi.register(quizId, displayName.trim());
      setJoined(true);
      toast.success("You're registered!");
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not register");
    }
  };

  const enterGame = async () => {
    try {
      await quizApi.join(quizId);
      navigate(`/quizzes/${quizId}/play`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Cannot join yet");
    }
  };

  if (!quiz) return <div className="page-bg"><TopBar /><p className="p-8 text-slate-500">Loading...</p></div>;

  return (
    <div className="page-bg">
      <TopBar />
      <main className="max-w-3xl mx-auto px-4 py-10">
        <div className="flex items-center justify-between gap-2 mb-1">
          <h1 className="section-title">{quiz.title}</h1>
          <StatusBadge status={quiz.status} />
        </div>
        <p className="section-sub mb-8">{quiz.description}</p>

        <div className="card p-6 mb-8">
          {quiz.status === "finished" ? (
            <div className="text-center py-6">
              <p className="font-semibold text-slate-800">This quiz has ended</p>
              <p className="text-sm text-slate-500 mt-1">Registration is closed.</p>
            </div>
          ) : !joined ? (
            <div className="space-y-3">
              <label className="text-sm font-medium text-slate-700">Your display name</label>
              <input className="input-field" placeholder="e.g. Alex" value={displayName}
                onChange={(e) => setDisplayName(e.target.value)} />
              <button onClick={register} disabled={!displayName.trim()} className="btn-primary w-full">
                Register for this quiz
              </button>
            </div>
          ) : quiz.status === "live" ? (
            <button onClick={enterGame} className="btn-success w-full py-3 text-base animate-pulse-ring">
              The quiz is live — Enter now
            </button>
          ) : (
            <div className="text-center py-6">
              <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-indigo-50 border border-indigo-100 flex items-center justify-center">
                <div className="w-5 h-5 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
              </div>
              <p className="font-semibold text-slate-800">You're registered</p>
              <p className="text-sm text-slate-500 mt-1">Waiting for the organizer to start. Updates automatically.</p>
            </div>
          )}
        </div>

        <h2 className="text-sm font-semibold text-slate-700 mb-3">Registered players ({registered.length})</h2>
        <div className="flex flex-wrap gap-2">
          {registered.map((p, i) => (
            <span key={i} className="px-3 py-1.5 rounded-full bg-white border border-slate-200 text-sm text-slate-700 shadow-sm">
              {p.display_name}
            </span>
          ))}
          {registered.length === 0 && <p className="text-slate-400 text-sm">Be the first to register.</p>}
        </div>
      </main>
    </div>
  );
}
