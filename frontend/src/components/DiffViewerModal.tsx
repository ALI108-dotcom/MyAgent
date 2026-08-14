"use client";

import { FileChangeItem } from "@/types/agent";

interface DiffViewerModalProps {
  fileChange: FileChangeItem | null;
  onClose: () => void;
}

export function DiffViewerModal({ fileChange, onClose }: DiffViewerModalProps) {
  if (!fileChange) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-3xl w-full p-6 shadow-2xl relative flex flex-col max-h-[85vh]">
        <div className="flex justify-between items-center border-b border-slate-800 pb-3 mb-4">
          <div className="flex items-center gap-3">
            <h3 className="font-mono text-sm font-bold text-slate-100">{fileChange.file_path}</h3>
            <span
              className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase ${
                fileChange.change_type === "added"
                  ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                  : fileChange.change_type === "modified"
                  ? "bg-amber-950 text-amber-300 border border-amber-800"
                  : "bg-rose-950 text-rose-300 border border-rose-800"
              }`}
            >
              {fileChange.change_type}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-lg font-bold"
          >
            ×
          </button>
        </div>

        <div className="flex-1 overflow-y-auto font-mono text-xs bg-slate-950 p-4 rounded-lg border border-slate-800 text-slate-300 leading-relaxed whitespace-pre-wrap">
          {fileChange.snippet || "// No content preview available for this file."}
        </div>

        <div className="mt-4 flex justify-end">
          <button
            onClick={onClose}
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-4 py-2 rounded-lg font-medium transition-colors"
          >
            Close Diff View
          </button>
        </div>
      </div>
    </div>
  );
}
