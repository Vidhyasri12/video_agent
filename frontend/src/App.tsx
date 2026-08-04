import React, { useState } from "react";
import { VideoDemo } from "./components/VideoDemo/VideoDemo";
import { Tv, Upload, Bot, Settings, ShieldCheck, Activity } from "lucide-react";

export type AppTab = "camera" | "upload" | "assistant" | "settings";

export function App() {
  const [activeTab, setActiveTab] = useState<AppTab>("camera");

  return (
    <div className="min-h-screen flex flex-col bg-[#0b101d] text-slate-100 font-sans selection:bg-emerald-500 selection:text-slate-900 overflow-x-hidden">
      {/* VIGI VMS Sleek Header with Main Navigation Tabs */}
      <header className="bg-[#0f172a] border-b border-slate-800 flex-shrink-0 sticky top-0 z-50 shadow-lg">
        <div className="px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-4">
          
          {/* VIGI VMS Brand Logo */}
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-400 via-emerald-500 to-teal-600 flex items-center justify-center text-slate-950 shadow-md shadow-emerald-500/20 font-black">
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="font-extrabold text-base text-white tracking-wider font-mono">
                  VIGI VMS
                </h1>
                <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-[10px] font-mono font-bold rounded-full flex items-center space-x-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                  <span>ONLINE</span>
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">
                Surveillance Wall & AI Stream Intelligence
              </p>
            </div>
          </div>

          {/* Main Navigation Tabs */}
          <div className="flex items-center bg-[#070a12] p-1 rounded-xl border border-slate-800 space-x-1 shadow-inner">
            <button
              onClick={() => setActiveTab("camera")}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                activeTab === "camera"
                  ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <Tv className="w-4 h-4 text-emerald-300" />
              <span>Camera View</span>
            </button>

            <button
              onClick={() => setActiveTab("upload")}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                activeTab === "upload"
                  ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <Upload className="w-4 h-4 text-emerald-300" />
              <span>Upload Video</span>
            </button>

            <button
              onClick={() => setActiveTab("assistant")}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                activeTab === "assistant"
                  ? "bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-md shadow-emerald-600/30 font-extrabold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <Bot className="w-4 h-4 text-emerald-300" />
              <span>Video Assistant</span>
            </button>

            <button
              onClick={() => setActiveTab("settings")}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                activeTab === "settings"
                  ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <Settings className="w-4 h-4 text-emerald-300" />
              <span>Settings</span>
            </button>
          </div>

          {/* Right System Info Badge */}
          <div className="hidden md:flex items-center space-x-3 text-xs font-mono text-slate-400">
            <div className="flex items-center space-x-1.5 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
              <Activity className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
              <span>NVIDIA VSS AI</span>
            </div>
          </div>

        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 p-4 sm:p-6 overflow-auto">
        <VideoDemo activeTab={activeTab} setActiveTab={setActiveTab} />
      </main>
    </div>
  );
}

export default App;

