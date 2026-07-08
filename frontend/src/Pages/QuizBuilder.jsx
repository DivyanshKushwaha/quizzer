import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import { adminApi } from "../api";
import TopBar from "../components/TopBar";

const blankQuestion = () => ({
  text: "",
  options: ["", "", "", ""],
  correct_index: 0,
  timer_sec: 20,
});

const field = "input-field";

export default function QuizBuilder() {
  const { quizId } = useParams();
  const isEdit = quizId && quizId !== "new";
  const navigate = useNavigate();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [startAt, setStartAt] = useState("");
  const [perQuestion, setPerQuestion] = useState(20);
  const [overall, setOverall] = useState(300);
  const [winCondition, setWinCondition] = useState("score");
  const [prizeTop3, setPrizeTop3] = useState("");
  const [prizeTop10, setPrizeTop10] = useState("");
  const [questions, setQuestions] = useState([blankQuestion()]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!isEdit) return;
    adminApi
      .get(quizId)
      .then(({ data }) => {
        setTitle(data.title);
        setDescription(data.description || "");
        setPerQuestion(data.settings?.per_question_timer_sec ?? 20);
        setOverall(data.settings?.overall_timer_sec ?? 300);
        setWinCondition(data.settings?.win_condition ?? "score");
        setPrizeTop3(data.prize?.top3 ?? "");
        setPrizeTop10(data.prize?.top10 ?? "");
        setQuestions(data.questions?.length ? data.questions.map((q) => ({
          text: q.text,
          options: [...q.options, "", "", "", ""].slice(0, 4),
          correct_index: q.correct_index ?? 0,
          timer_sec: q.timer_sec ?? 20,
        })) : [blankQuestion()]);
      })
      .catch(() => {
        toast.error("Could not load quiz");
        navigate("/admin");
      });
  }, [quizId, isEdit, navigate]);

  const updateQ = (i, patch) =>
    setQuestions((qs) => qs.map((q, idx) => (idx === i ? { ...q, ...patch } : q)));

  const updateOption = (qi, oi, val) =>
    setQuestions((qs) =>
      qs.map((q, idx) =>
        idx === qi ? { ...q, options: q.options.map((o, k) => (k === oi ? val : o)) } : q
      )
    );

  const validate = () => {
    if (!title.trim()) return "Title is required";
    for (const [i, q] of questions.entries()) {
      if (!q.text.trim()) return `Question ${i + 1} needs text`;
      if (q.options.some((o) => !o.trim())) return `Question ${i + 1} needs all 4 options filled`;
    }
    return null;
  };

  const save = async () => {
    const err = validate();
    if (err) return toast.error(err);
    setBusy(true);
    const body = {
      title: title.trim(),
      description: description.trim(),
      settings: {
        per_question_timer_sec: Number(perQuestion),
        overall_timer_sec: Number(overall),
        win_condition: winCondition,
      },
      prize: { top3: prizeTop3.trim(), top10: prizeTop10.trim() },
      questions: questions.map((q) => ({
        text: q.text.trim(),
        options: q.options.map((o) => o.trim()),
        correct_index: Number(q.correct_index),
        timer_sec: Number(q.timer_sec),
      })),
      ...(startAt ? { start_at: new Date(startAt).toISOString() } : {}),
    };
    try {
      if (isEdit) await adminApi.update(quizId, body);
      else await adminApi.create(body);
      toast.success(isEdit ? "Quiz updated" : "Quiz created");
      navigate("/admin");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Save failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page-bg">
      <TopBar />
      <main className="max-w-3xl mx-auto px-4 py-10">
        <h1 className="section-title mb-8">{isEdit ? "Edit quiz" : "Create quiz"}</h1>

        <section className="card p-5 mb-5 space-y-3">
          <input className={field} placeholder="Quiz title" value={title} onChange={(e) => setTitle(e.target.value)} />
          <textarea className={field} rows={2} placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
          <label className="text-sm block">
            <span className="text-slate-500 text-xs">Scheduled start (auto-goes live at this time)</span>
            <input type="datetime-local" className={field} value={startAt} onChange={(e) => setStartAt(e.target.value)} />
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="text-sm">
              <span className="text-slate-500 text-xs">Per-question timer (sec)</span>
              <input type="number" min={5} className={field} value={perQuestion} onChange={(e) => setPerQuestion(e.target.value)} />
            </label>
            <label className="text-sm">
              <span className="text-slate-500 text-xs">Overall timer (sec)</span>
              <input type="number" min={0} className={field} value={overall} onChange={(e) => setOverall(e.target.value)} />
            </label>
          </div>
          <label className="text-sm block">
            <span className="text-slate-500 text-xs">Win condition</span>
            <select className={field} value={winCondition} onChange={(e) => setWinCondition(e.target.value)}>
              <option value="score">Highest score (ties: fastest)</option>
              <option value="speed">Fastest correct completion</option>
            </select>
          </label>
          <div className="grid grid-cols-2 gap-3">
            <input className={field} placeholder="Top-3 prize" value={prizeTop3} onChange={(e) => setPrizeTop3(e.target.value)} />
            <input className={field} placeholder="Top-10 prize" value={prizeTop10} onChange={(e) => setPrizeTop10(e.target.value)} />
          </div>
        </section>

        <div className="space-y-4">
          {questions.map((q, qi) => (
            <section key={qi} className="card p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-slate-800">Question {qi + 1}</h3>
                {questions.length > 1 && (
                  <button onClick={() => setQuestions((qs) => qs.filter((_, i) => i !== qi))} className="text-xs text-red-500 hover:underline">
                    Remove
                  </button>
                )}
              </div>
              <input className={`${field} mb-3`} placeholder="Question text" value={q.text} onChange={(e) => updateQ(qi, { text: e.target.value })} />
              <div className="space-y-2">
                {q.options.map((opt, oi) => (
                  <div key={oi} className="flex items-center gap-2">
                    <input type="radio" name={`correct-${qi}`} checked={Number(q.correct_index) === oi}
                      onChange={() => updateQ(qi, { correct_index: oi })} className="accent-indigo-600" />
                    <span className="text-slate-500 text-sm w-4 font-medium">{String.fromCharCode(65 + oi)}</span>
                    <input className={field} placeholder={`Option ${oi + 1}`} value={opt} onChange={(e) => updateOption(qi, oi, e.target.value)} />
                  </div>
                ))}
              </div>
              <label className="text-sm mt-3 inline-flex items-center gap-2">
                <span className="text-slate-500 text-xs">Timer (sec)</span>
                <input type="number" min={5} className="w-24 input-field py-1.5" value={q.timer_sec}
                  onChange={(e) => updateQ(qi, { timer_sec: e.target.value })} />
              </label>
              <p className="text-xs text-slate-400 mt-2">Select the radio next to the correct option.</p>
            </section>
          ))}
        </div>

        <button onClick={() => setQuestions((qs) => [...qs, blankQuestion()])}
          className="mt-4 w-full py-2.5 rounded-xl border border-dashed border-slate-300 text-slate-500 hover:border-indigo-300 hover:text-indigo-600 text-sm transition bg-white">
          + Add question
        </button>

        <div className="mt-6 flex gap-3">
          <button onClick={() => navigate("/admin")} className="btn-secondary">Cancel</button>
          <button onClick={save} disabled={busy} className="btn-primary flex-1">
            {busy ? "Saving..." : isEdit ? "Save changes" : "Create quiz"}
          </button>
        </div>
      </main>
    </div>
  );
}
