"use client";

interface WelcomeScreenProps {
  onSelectPrompt: (promptText: string) => void;
}

export function WelcomeScreen({ onSelectPrompt }: WelcomeScreenProps) {
  const suggestions = [
    {
      title: "🧮 Build Calculator & Run Tests",
      desc: "Creates calculator.py, test suite, runs pytest, and reports results.",
      prompt:
        "Create a small Python calculator module with add, subtract, multiply and divide functions. Create tests for it, run the tests, and explain what you created.",
    },
    {
      title: "🔍 Inspect & Explain Architecture",
      desc: "Scans project files and statically analyzes backend architecture.",
      prompt: "Inspect this project and explain its architecture.",
    },
    {
      title: "🔒 Build Auth & Security Flow",
      desc: "Implements secure JWT bearer authentication and user RBAC.",
      prompt: "Build a FastAPI authentication and user authorization system.",
    },
    {
      title: "🐛 Debug & Fix Test Failures",
      desc: "Runs test suite, diagnoses errors, and fixes broken code path.",
      prompt: "Run the project tests, find any failing tests, and fix them.",
    },
  ];

  return (
    <div className="max-w-3xl mx-auto px-4 py-12 text-center space-y-8 select-none my-auto">
      {/* ALI Emblem Header */}
      <div className="space-y-3">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 via-teal-500 to-indigo-600 flex items-center justify-center font-black text-2xl text-white mx-auto shadow-2xl tracking-tight">
          M
        </div>
        <h1 className="text-3xl font-extrabold text-slate-100 tracking-tight">
          How can I help you code today?
        </h1>
        <p className="text-sm text-slate-400 max-w-md mx-auto">
          I&apos;m MyAgent, your personal AI software engineer. Ask me to build modules, fix bugs, inspect architecture, or run tests.
        </p>
      </div>

      {/* Suggested Prompt Chips */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl mx-auto pt-2 text-left">
        {suggestions.map((item, idx) => (
          <button
            key={idx}
            onClick={() => onSelectPrompt(item.prompt)}
            className="bg-slate-900/80 hover:bg-slate-800/90 border border-slate-800/90 hover:border-slate-700 p-4 rounded-xl transition-all group shadow-sm flex flex-col justify-between"
          >
            <div>
              <div className="text-xs font-bold text-blue-400 group-hover:text-blue-300">
                {item.title}
              </div>
              <div className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                {item.desc}
              </div>
            </div>
            <div className="text-[10px] text-slate-500 font-mono mt-3 flex items-center gap-1 group-hover:text-slate-400">
              <span>Use prompt</span>
              <span>→</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
