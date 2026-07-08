export default function AuthShell({ title, subtitle, children }) {
  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-slate-50 via-white to-indigo-50">
      <div className="w-full max-w-md animate-pop-in">
        <div className="text-center mb-6">
          <div className="text-2xl font-extrabold tracking-tight text-slate-900">QuizArena</div>
          <h1 className="mt-4 text-xl font-bold text-slate-800">{title}</h1>
          {subtitle && <p className="text-sm text-slate-500 mt-1">{subtitle}</p>}
        </div>
        <div className="card p-6 shadow-lg shadow-slate-200/60">{children}</div>
      </div>
    </div>
  );
}

export const inputClass = "input-field";
export const btnClass = "btn-primary w-full";
