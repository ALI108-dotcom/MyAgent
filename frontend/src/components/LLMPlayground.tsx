"use client";

import { useState } from "react";
import { generateLLMCompletion } from "@/lib/api";
import { LLMResponse } from "@/types/llm";

export function LLMPlayground() {
  const [prompt, setPrompt] = useState<string>("Write a Python function to check if a string is a palindrome.");
  const [systemPrompt, setSystemPrompt] = useState<string>("You are ALI, my personal AI Software Engineer.");
  const [provider, setProvider] = useState<"mock" | "gemini" | "openai">("mock");
  const [temperature, setTemperature] = useState<number>(0.7);
  const [loading, setLoading] = useState<boolean>(false);
  const [response, setResponse] = useState<LLMResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [latency, setLatency] = useState<number | null>(null);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);
    const startTime = performance.now();

    try {
      const res = await generateLLMCompletion({
        prompt,
        system_prompt: systemPrompt.trim() || undefined,
        provider,
        temperature,
      });
      const endTime = performance.now();
      setResponse(res);
      setLatency(Math.round(endTime - startTime));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Generation failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-2">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <span>🤖</span> LLM Subsystem Testing Playground
          </h2>
          <p className="text-slate-400 text-xs mt-1">
            Test prompt completions via backend abstraction layer (<code className="text-blue-400 font-mono">app.agent.llm</code>).
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

      <form onSubmit={handleGenerate} className="space-y-4">
        {/* System Prompt Input */}
        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1">
            System Instruction (Optional)
          </label>
          <input
            type="text"
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            placeholder="e.g. You are a senior Python mentor..."
            className="w-full bg-slate-950/90 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
          />
        </div>

        {/* User Prompt Input */}
        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1">User Prompt</label>
          <textarea
            rows={3}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Type your prompt here..."
            className="w-full bg-slate-950/90 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500 font-sans"
            required
          />
        </div>

        {/* Temperature slider & Generate Button */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-1">
          <div className="flex items-center gap-3">
            <label className="text-xs font-mono text-slate-400">
              Temperature: <span className="text-blue-400 font-bold">{temperature}</span>
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              className="w-24 accent-blue-500 cursor-pointer"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !prompt.trim()}
            className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-sm font-semibold rounded-xl shadow-lg transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <span className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                Generating...
              </>
            ) : (
              "Generate Completion"
            )}
          </button>
        </div>
      </form>

      {/* Error display */}
      {error && (
        <div className="mt-5 p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs font-mono">
          <div className="font-bold mb-1">⚠️ Error Generating Completion:</div>
          <div>{error}</div>
        </div>
      )}

      {/* Response display */}
      {response && (
        <div className="mt-6 pt-6 border-t border-slate-800">
          <div className="flex flex-wrap justify-between items-center gap-2 mb-3">
            <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
              <span className="text-emerald-400 font-bold">✓ Generation Complete</span>
              <span>• Provider: <code className="text-blue-400">{response.provider}</code></span>
              <span>• Model: <code className="text-indigo-400">{response.model}</code></span>
            </div>
            <div className="text-xs font-mono text-slate-500">
              Tokens: <span className="text-slate-300">{response.usage.total_tokens}</span> (P: {response.usage.prompt_tokens} / C: {response.usage.completion_tokens}) | {latency}ms
            </div>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 font-mono text-xs text-slate-200 whitespace-pre-wrap leading-relaxed overflow-x-auto">
            {response.content}
          </div>
        </div>
      )}
    </div>
  );
}
