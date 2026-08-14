"use client";

import { useState } from "react";
import { DiffViewerModal } from "@/components/DiffViewerModal";
import { AgentStatus, FileChangeItem, TestResultItem } from "@/types/agent";

interface AgentPanelProps {
  status: AgentStatus;
  plan: string[];
  fileChanges: FileChangeItem[];
  testResults: TestResultItem | null;
  pendingApproval: { taskId: string; action: string } | null;
  onApprove: (approved: boolean) => void;
}

export function AgentPanel({
  status,
  plan,
  fileChanges,
  testResults,
  pendingApproval,
  onApprove,
}: AgentPanelProps) {
  const [selectedDiffFile, setSelectedDiffFile] = useState<FileChangeItem | null>(null);

  function getStatusBadge(st: AgentStatus) {
    switch (st) {
      case "ready":
        return { label: "🟢 Ready", color: "bg-emerald-950 text-emerald-300 border-emerald-800" };
      case "thinking":
        return { label: "🔵 Thinking...", color: "bg-blue-950 text-blue-300 border-blue-800 animate-pulse" };
      case "planning":
        return { label: "🔵 Planning...", color: "bg-indigo-950 text-indigo-300 border-indigo-800 animate-pulse" };
      case "inspecting":
        return { label: "🟡 Inspecting Code...", color: "bg-amber-950 text-amber-300 border-amber-800 animate-pulse" };
      case "editing_files":
        return { label: "🟡 Editing Files...", color: "bg-amber-950 text-amber-300 border-amber-800 animate-pulse" };
      case "running_tests":
        return { label: "🟡 Running Tests...", color: "bg-amber-950 text-amber-300 border-amber-800 animate-pulse" };
      case "approval_required":
        return { label: "⚠️ Approval Required", color: "bg-rose-950 text-rose-300 border-rose-800 animate-bounce" };
      case "completed":
        return { label: "🟢 Task Completed", color: "bg-emerald-950 text-emerald-300 border-emerald-800" };
      case "error":
        return { label: "🔴 Task Failed", color: "bg-rose-950 text-rose-300 border-rose-800" };
      default:
        return { label: "Ready", color: "bg-slate-800 text-slate-300 border-slate-700" };
    }
  }

  const badge = getStatusBadge(status);

  return (
    <aside className="w-80 bg-slate-950 border-l border-slate-800/80 flex flex-col h-screen p-4 select-none shrink-0 overflow-y-auto space-y-4">
      {/* Top Agent Status Badge */}
      <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-xl flex justify-between items-center shadow-sm">
        <span className="text-xs font-bold text-slate-300">Agent Status</span>
        <span
          className={`text-xs px-2.5 py-1 font-semibold rounded-md border font-mono ${badge.color}`}
        >
          {badge.label}
        </span>
      </div>

      {/* Human Approval Required Banner */}
      {pendingApproval && (
        <div className="bg-rose-950/90 border border-rose-700 rounded-xl p-3.5 shadow-lg animate-pulse">
          <div className="text-xs font-bold text-rose-200 mb-1">⚠️ Approval Required</div>
          <p className="text-[11px] text-rose-300 mb-3">
            ALI wants to execute: <code className="font-mono">{pendingApproval.action}</code>
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => onApprove(true)}
              className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs py-1.5 rounded-lg transition-colors"
            >
              Approve
            </button>
            <button
              onClick={() => onApprove(false)}
              className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs py-1.5 rounded-lg transition-colors"
            >
              Reject
            </button>
          </div>
        </div>
      )}

      {/* Step-by-Step Plan Progress Checklist */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-sm">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2.5 flex justify-between items-center">
          <span>Execution Plan</span>
          <span className="text-[10px] text-slate-500 font-mono">{plan.length} Steps</span>
        </h3>

        {plan.length === 0 ? (
          <div className="text-[11px] text-slate-500 italic py-2">No active plan yet.</div>
        ) : (
          <div className="space-y-2">
            {plan.map((stepText, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2 text-xs text-slate-300 bg-slate-950 p-2 rounded-lg border border-slate-800/80 font-mono"
              >
                <span className="text-blue-400 font-bold">✓</span>
                <span>{stepText}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modified Files Section */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-sm">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2.5 flex justify-between items-center">
          <span>Files Changed</span>
          <span className="text-[10px] text-slate-500 font-mono">{fileChanges.length} Files</span>
        </h3>

        {fileChanges.length === 0 ? (
          <div className="text-[11px] text-slate-500 italic py-2">No modified files.</div>
        ) : (
          <div className="space-y-2">
            {fileChanges.map((file, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between bg-slate-950 p-2.5 rounded-lg border border-slate-800/80 font-mono text-xs"
              >
                <div className="truncate max-w-[170px] text-slate-200">
                  <span
                    className={`mr-1.5 font-bold ${
                      file.change_type === "added"
                        ? "text-emerald-400"
                        : file.change_type === "modified"
                        ? "text-amber-400"
                        : "text-rose-400"
                    }`}
                  >
                    {file.change_type === "added" ? "+" : file.change_type === "modified" ? "~" : "-"}
                  </span>
                  {file.file_path}
                </div>

                <button
                  onClick={() => setSelectedDiffFile(file)}
                  className="text-[10px] bg-slate-800 hover:bg-slate-700 text-blue-400 px-2 py-0.5 rounded transition-colors"
                >
                  View Diff
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Test Execution Summary */}
      {testResults && (
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-sm">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2.5">
            Test Execution Results
          </h3>
          <div className="flex gap-2 mb-3">
            <div className="flex-1 bg-emerald-950/60 border border-emerald-800/80 p-2 rounded-lg text-center">
              <div className="text-base font-extrabold text-emerald-400">{testResults.passed}</div>
              <div className="text-[10px] text-emerald-300 font-semibold uppercase">Passed</div>
            </div>

            <div className="flex-1 bg-rose-950/60 border border-rose-800/80 p-2 rounded-lg text-center">
              <div className="text-base font-extrabold text-rose-400">{testResults.failed}</div>
              <div className="text-[10px] text-rose-300 font-semibold uppercase">Failed</div>
            </div>
          </div>

          <details className="text-xs text-slate-400 bg-slate-950 p-2.5 rounded-lg border border-slate-800">
            <summary className="font-mono cursor-pointer font-semibold text-slate-300">
              Pytest Console Output
            </summary>
            <pre className="font-mono text-[10px] text-slate-400 mt-2 whitespace-pre-wrap overflow-x-auto max-h-36">
              {testResults.output}
            </pre>
          </details>
        </div>
      )}

      {/* Diff Viewer Modal */}
      <DiffViewerModal
        fileChange={selectedDiffFile}
        onClose={() => setSelectedDiffFile(null)}
      />
    </aside>
  );
}
