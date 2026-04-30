export function StatusBar() {
  return (
    <div className="fixed bottom-0 left-0 right-0 h-8 bg-slate-50 border-t border-cyan-100 flex items-center justify-between px-4 z-50 md:pl-64">
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <span className="font-mono text-[11px] text-slate-400">
          AIRO v0.1.0 · LangGraph · Groq · MLflow
        </span>
      </div>
      <div className="hidden sm:block">
        <span className="font-mono text-[11px] text-slate-400">
          BSAI · Dawood University · 2026
        </span>
      </div>
    </div>
  )
}
