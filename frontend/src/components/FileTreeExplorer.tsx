"use client";

import { useEffect, useState } from "react";
import { fetchProjectContext } from "@/lib/api";
import { ProjectContext } from "@/types/memory";

export function FileTreeExplorer() {
  const [context, setContext] = useState<ProjectContext | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadContext();
  }, []);

  async function loadContext() {
    try {
      const data = await fetchProjectContext();
      setContext(data);
    } catch (e) {
      console.error("Failed to load workspace file tree:", e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 flex flex-col h-full">
      <div className="flex justify-between items-center mb-2 pb-2 border-b border-slate-800">
        <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Workspace Files
        </span>
        <button
          onClick={loadContext}
          className="text-[10px] text-blue-400 hover:text-blue-300 transition-colors"
        >
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="space-y-1.5 py-2">
          <div className="h-4 bg-slate-800/60 rounded animate-pulse w-3/4" />
          <div className="h-4 bg-slate-800/60 rounded animate-pulse w-1/2" />
          <div className="h-4 bg-slate-800/60 rounded animate-pulse w-2/3" />
        </div>
      ) : context ? (
        <div className="flex-1 overflow-y-auto space-y-1 font-mono text-xs text-slate-400">
          {context.key_files.map((file) => (
            <div
              key={file}
              className="flex items-center gap-2 hover:bg-slate-800/60 px-2 py-1 rounded cursor-pointer transition-colors text-slate-300"
            >
              <span className="text-blue-400 text-[10px]">📄</span>
              <span className="truncate">{file}</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-[11px] text-slate-500 py-2">No files scanned yet.</div>
      )}
    </div>
  );
}
