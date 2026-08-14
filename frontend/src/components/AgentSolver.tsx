"use client";

import { useState } from "react";
import { solveAgentGoal } from "@/lib/api";
import { ReasoningResponse } from "@/types/reasoning";

export function AgentSolver() {
  const [goal, setGoal] = useState<string>("Inspect workspace code structure and run automated tests");
  const [context, setContext] = useState<string>("Operating inside Personal AI Coding Agent project");
  const [provider, setProvider] = useState<"mock" | "gemini" | "openai">("mock");
  const [loading, setLoading] = useState<boolean>(false);
  const [response, setResponse] = useState<ReasoningResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await solveAgentGoal({
        goal,
        context: context.trim() || undefined,
        provider,
      });
      setResponse(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Autonomous goal solving failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const setPresetGoal = (presetGoal: string) => {
    setGoal(presetGoal);
    setResponse(null);
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-2">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <span>🧠</span> ReAct Cognitive Agent Solver
          </h2>
          <p className="text-slate-400 text-xs mt-1">
            Autonomous goal solver orchestrating reasoning and tool executions in <code className="text-blue-400 font-mono">backend/app/agent/reasoning/</code>.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-400 font-mono">Provider:</label>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value as "mock" | "gemini" | "openai")}
            className="bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-blue-500 font-mono"
          >
            <option value="mock">mock (Offline / Free)</option>
            <option value="gemini">gemini (Google API)</option>
            <option value="openai">openai (OpenAI API)</option>
          </select>
        </div>
      </div>

      {/* Preset Quick Goals */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <span className="text-xs font-mono text-slate-400">Presets:</span>
        <button
          type="button"
          onClick={() => setPresetGoal("Inspect workspace code structure and run automated tests")}
          className="text-xs bg-slate-950 hover:bg-slate-800 text-blue-400 px-3 py-1 rounded-full border border-slate-800 transition-all font-mono"
        >
          Inspect &amp; Test Workspace
        </button>
        <button
          type="button"
          onClick={() => setPresetGoal("Analyze backend/app/main.py architecture using AST inspection")}
          className="text-xs bg-slate-950 hover:bg-slate-800 text-teal-400 px-3 py-1 rounded-full border border-slate-800 transition-all font-mono"
        >
          Inspect backend/app/main.py
        </button>
        <button
          type="button"
          onClick={() => setPresetGoal("Read project README.md documentation guidelines")}
          className="text-xs bg-slate-950 hover:bg-slate-800 text-indigo-400 px-3 py-1 rounded-full border border-slate-800 transition-all font-mono"
        >
          Read Documentation
        </button>
      </div>

      <form onSubmit={handleSolve} className="space-y-4">
        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1">
            Software Engineering Goal <span className="text-rose-400">*</span>
          </label>
          <input
            type="text"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="e.g. Inspect backend files and execute unit tests..."
            className="w-full bg-slate-950/90 border border-slate-800 rounded-lg px-3 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-blue-500 font-sans"
            required
          />
        </div>

        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1">
            Extra Background Context (Optional)
          </label>
          <input
            type="text"
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="Additional context instructions..."
            className="w-full bg-slate-950/90 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-blue-500 font-mono"
          />
        </div>

        <div className="flex justify-end pt-1">
          <button
            type="submit"
            disabled={loading || !goal.trim()}
            className="px-6 py-2.5 bg-gradient-to-r from-teal-600 via-blue-600 to-indigo-600 hover:from-teal-500 hover:to-indigo-500 text-white text-sm font-semibold rounded-xl shadow-lg transition-all disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? (
              <>
                <span className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                Autonomous Engine Solving...
              </>
            ) : (
              "⚡ Run ReAct Cognitive Engine"
            )}
          </button>
        </div>
      </form>

      {/* Error display */}
      {error && (
        <div className="mt-5 p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs font-mono">
          <div className="font-bold mb-1">⚠️ Goal Solver Error:</div>
          <div>{error}</div>
        </div>
      )}

      {/* Solver Trajectory and Answer Display */}
      {response && (
        <div className="mt-6 pt-6 border-t border-slate-800 space-y-6">
          <div className="flex flex-wrap justify-between items-center gap-2">
            <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 font-bold">
              <span>✓ Goal Solved Successfully</span>
              <span className="text-slate-500 font-normal">
                ({response.total_iterations} Reasoning Steps | {response.execution_time_ms.toFixed(1)} ms)
              </span>
            </div>
            <div className="text-[11px] font-mono text-slate-500">
              {new Date(response.timestamp).toLocaleTimeString()}
            </div>
          </div>

          {/* Reasoning Trajectory Steps */}
          <div className="space-y-3">
            <div className="text-xs font-mono text-slate-400 font-bold uppercase">
              Reasoning &amp; Action Trajectory
            </div>
            {response.trajectory.map((step) => (
              <div
                key={step.step_number}
                className="bg-slate-950 border border-slate-800/80 rounded-xl p-4 space-y-2 font-mono text-xs"
              >
                <div className="flex justify-between items-center">
                  <span className="font-bold text-blue-400">
                    Step {step.step_number}: {step.tool_name ? `Invoked tool [${step.tool_name}]` : "Thought Process"}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${
                      step.status === "completed"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                        : "bg-rose-500/10 text-rose-400 border-rose-500/30"
                    }`}
                  >
                    {step.status}
                  </span>
                </div>

                <div className="text-slate-300">
                  <span className="text-slate-500 font-bold">Thought: </span>
                  {step.thought}
                </div>

                {step.tool_params && (
                  <div className="text-[11px] text-slate-400 bg-slate-900/60 p-2 rounded border border-slate-800/60">
                    <span className="text-slate-500 font-bold">Params: </span>
                    {JSON.stringify(step.tool_params)}
                  </div>
                )}

                {step.observation && (
                  <div className="mt-2 bg-slate-900/90 border border-slate-800 rounded p-3 text-slate-300 font-mono text-[11px] whitespace-pre-wrap max-h-48 overflow-y-auto">
                    <div className="text-slate-500 font-bold mb-1">Observation:</div>
                    {step.observation}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Final Answer */}
          <div className="bg-gradient-to-br from-slate-950 to-slate-900 border border-blue-500/30 rounded-xl p-5 shadow-lg">
            <h3 className="text-sm font-bold font-mono text-blue-400 mb-2 uppercase tracking-wider flex items-center gap-2">
              <span>🎯</span> Final Resolution &amp; Synthesis
            </h3>
            <div className="font-mono text-xs text-slate-100 whitespace-pre-wrap leading-relaxed">
              {response.final_answer}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
