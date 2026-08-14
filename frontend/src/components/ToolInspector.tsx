"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchAvailableTools, executeTool } from "@/lib/api";
import { ToolDefinition, ToolResult } from "@/types/tool";

export function ToolInspector() {
  const [tools, setTools] = useState<ToolDefinition[]>([]);
  const [selectedToolName, setSelectedToolName] = useState<string>("");
  const [paramInputs, setParamInputs] = useState<Record<string, string>>({});
  const [loadingTools, setLoadingTools] = useState<boolean>(true);
  const [executing, setExecuting] = useState<boolean>(false);
  const [result, setResult] = useState<ToolResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const initParamsForTool = useCallback((tool: ToolDefinition) => {
    const initial: Record<string, string> = {};
    Object.entries(tool.parameters).forEach(([paramName, spec]) => {
      initial[paramName] = spec.default !== undefined && spec.default !== null ? String(spec.default) : "";
    });

    if (tool.name === "read_file" && !initial.path) initial.path = "README.md";
    if (tool.name === "list_directory" && !initial.path) initial.path = ".";
    if (tool.name === "inspect_code" && !initial.path) initial.path = "backend/app/main.py";
    if (tool.name === "run_command" && !initial.command) initial.command = "python --version";
    if (tool.name === "write_file") {
      if (!initial.path) initial.path = "backend/tests/scratch_demo.txt";
      if (!initial.content) initial.content = "Sample content generated via ToolInspector UI";
    }

    setParamInputs(initial);
  }, []);

  const loadTools = useCallback(async () => {
    setLoadingTools(true);
    setError(null);
    try {
      const data = await fetchAvailableTools();
      setTools(data);
      if (data.length > 0) {
        setSelectedToolName(data[0].name);
        initParamsForTool(data[0]);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load tools";
      setError(msg);
    } finally {
      setLoadingTools(false);
    }
  }, [initParamsForTool]);

  useEffect(() => {
    loadTools();
  }, [loadTools]);

  const handleToolSelect = (toolName: string) => {
    setSelectedToolName(toolName);
    const target = tools.find((t) => t.name === toolName);
    if (target) {
      initParamsForTool(target);
    }
    setResult(null);
  };

  const handleParamChange = (paramName: string, value: string) => {
    setParamInputs((prev) => ({ ...prev, [paramName]: value }));
  };

  const handleExecute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedToolName) return;

    setExecuting(true);
    setError(null);
    setResult(null);

    const parsedParams: Record<string, unknown> = {};
    const currentTool = tools.find((t) => t.name === selectedToolName);

    if (currentTool) {
      Object.entries(currentTool.parameters).forEach(([paramName, spec]) => {
        const rawVal = paramInputs[paramName];
        if (rawVal !== undefined && rawVal !== "") {
          if (spec.type === "integer" || spec.type === "number") {
            parsedParams[paramName] = Number(rawVal);
          } else if (spec.type === "boolean") {
            parsedParams[paramName] = rawVal === "true";
          } else {
            parsedParams[paramName] = rawVal;
          }
        }
      });
    }

    try {
      const res = await executeTool({
        tool_name: selectedToolName,
        parameters: parsedParams,
      });
      setResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Tool execution failed";
      setError(msg);
    } finally {
      setExecuting(false);
    }
  };

  const selectedTool = tools.find((t) => t.name === selectedToolName);

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-2">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <span>🛠️</span> Safe Tool Execution Subsystem
          </h2>
          <p className="text-slate-400 text-xs mt-1">
            Registered Agent Tools in <code className="text-blue-400 font-mono">backend/app/agent/tools/</code> with workspace security boundaries.
          </p>
        </div>

        <button
          onClick={loadTools}
          disabled={loadingTools}
          className="text-xs px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono rounded-lg transition-all border border-slate-700 disabled:opacity-50"
        >
          {loadingTools ? "Refreshing..." : "Reload Tool Registry"}
        </button>
      </div>

      {loadingTools ? (
        <div className="text-slate-400 text-xs font-mono py-6 text-center animate-pulse">
          Discovering registered agent tools...
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Tool Selection List */}
          <div className="lg:col-span-4 bg-slate-950 border border-slate-800 rounded-xl p-3">
            <div className="text-xs font-mono text-slate-400 font-bold uppercase mb-2 px-2">
              Available Tools ({tools.length})
            </div>
            <div className="space-y-1">
              {tools.map((t) => (
                <button
                  key={t.name}
                  onClick={() => handleToolSelect(t.name)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg transition-all font-mono text-xs flex justify-between items-center ${
                    selectedToolName === t.name
                      ? "bg-blue-600/20 text-blue-300 border border-blue-500/40"
                      : "text-slate-300 hover:bg-slate-900 border border-transparent"
                  }`}
                >
                  <span className="font-semibold">{t.name}</span>
                  <span className="text-[10px] text-slate-500 font-normal truncate max-w-[100px]">
                    {Object.keys(t.parameters).length} args
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Form & Inspector */}
          <div className="lg:col-span-8 space-y-4">
            {selectedTool && (
              <form onSubmit={handleExecute} className="space-y-4 bg-slate-950/60 border border-slate-800 rounded-xl p-4">
                <div>
                  <div className="text-sm font-bold font-mono text-blue-400">{selectedTool.name}</div>
                  <p className="text-xs text-slate-400 mt-1">{selectedTool.description}</p>
                </div>

                {/* Parameters Form */}
                <div className="space-y-3 pt-2">
                  <div className="text-xs font-mono text-slate-400 font-bold uppercase">Parameters</div>
                  {Object.entries(selectedTool.parameters).map(([paramName, spec]) => (
                    <div key={paramName}>
                      <label className="block text-xs font-mono text-slate-300 mb-1">
                        {paramName}{" "}
                        {spec.required ? (
                          <span className="text-rose-400">*</span>
                        ) : (
                          <span className="text-slate-500">(optional)</span>
                        )}
                        <span className="text-slate-500 font-normal ml-2">— {spec.description}</span>
                      </label>
                      {paramName === "content" || paramName === "code" ? (
                        <textarea
                          rows={3}
                          value={paramInputs[paramName] || ""}
                          onChange={(e) => handleParamChange(paramName, e.target.value)}
                          className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-blue-500"
                        />
                      ) : (
                        <input
                          type="text"
                          value={paramInputs[paramName] || ""}
                          onChange={(e) => handleParamChange(paramName, e.target.value)}
                          placeholder={spec.default !== undefined ? String(spec.default) : ""}
                          className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-blue-500"
                        />
                      )}
                    </div>
                  ))}
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    type="submit"
                    disabled={executing}
                    className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-mono font-bold rounded-lg transition-all shadow-md disabled:opacity-50 flex items-center gap-2"
                  >
                    {executing ? (
                      <>
                        <span className="animate-spin rounded-full h-3 w-3 border-2 border-white border-t-transparent" />
                        Executing Tool...
                      </>
                    ) : (
                      `▶ Execute ${selectedTool.name}`
                    )}
                  </button>
                </div>
              </form>
            )}

            {/* Error display */}
            {error && (
              <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs font-mono">
                <div className="font-bold mb-1">⚠️ Tool Execution Error:</div>
                <div>{error}</div>
              </div>
            )}

            {/* Tool Output Display */}
            {result && (
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 font-mono text-xs">
                <div className="flex justify-between items-center mb-3 pb-2 border-b border-slate-800">
                  <span className={`font-bold ${result.success ? "text-emerald-400" : "text-rose-400"}`}>
                    {result.success ? "✓ Execution Succeeded" : "❌ Execution Failed"}
                  </span>
                  <span className="text-slate-500 text-[11px]">
                    {result.execution_time_ms.toFixed(2)} ms | {new Date(result.timestamp).toLocaleTimeString()}
                  </span>
                </div>

                {result.error && (
                  <div className="mb-3 p-2 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded">
                    {result.error}
                  </div>
                )}

                <pre className="text-slate-200 whitespace-pre-wrap leading-relaxed overflow-x-auto max-h-80">
                  {result.output}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
