export default function Loading() {
  return (
    <div className="min-h-screen bg-[rgb(15,17,26)] flex flex-col items-center justify-center gap-6">
      {/* Logo */}
      <div className="relative">
        <div className="w-16 h-16 rounded-2xl bg-portal-600 flex items-center justify-center shadow-lg glow animate-pulse">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
          </svg>
        </div>
        {/* Orbiting dot */}
        <div className="absolute inset-0 animate-spin" style={{ animationDuration: "3s" }}>
          <div className="absolute -top-1 left-1/2 w-2.5 h-2.5 rounded-full bg-portal-400 -translate-x-1/2" />
        </div>
      </div>

      {/* Title */}
      <div className="text-center">
        <h1 className="text-2xl font-bold text-slate-100 tracking-wide">PortalAI</h1>
        <p className="text-sm text-slate-400 mt-1">Portaldot AI Copilot</p>
      </div>

      {/* Loading bar */}
      <div className="w-48 h-1 bg-slate-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-portal-600 to-portal-400 rounded-full"
          style={{
            animation: "loadingBar 1.8s ease-in-out infinite",
          }}
        />
      </div>

      <p className="text-xs text-slate-600 animate-pulse">Connecting to Portaldot…</p>

      <style>{`
        @keyframes loadingBar {
          0%   { width: 0%;   margin-left: 0%; }
          50%  { width: 60%;  margin-left: 20%; }
          100% { width: 0%;   margin-left: 100%; }
        }
      `}</style>
    </div>
  );
}
