"use client";

import { AuthWidget } from "@/components/AuthWidget";
import { FileTreeExplorer } from "@/components/FileTreeExplorer";
import { TaskRecord } from "@/types/agent";

interface SidebarProps {
  tasks: TaskRecord[];
  activeTaskId: string | null;
  onSelectTask: (taskId: string) => void;
  onNewTask: () => void;
}

export function Sidebar({ tasks, activeTaskId, onSelectTask, onNewTask }: SidebarProps) {
  return (
    <aside className="w-72 bg-slate-950 border-r border-slate-800/80 flex flex-col h-screen p-4 select-none shrink-0">
      {/* ALI Branding Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800/80 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-tr from-blue-600 to-emerald-400 flex items-center justify-center font-black text-white text-xs shadow-md">
              A
            </div>
            <span className="font-extrabold text-base tracking-tight bg-gradient-to-r from-blue-400 to-teal-300 bg-clip-text text-transparent">
              ALI Agent
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-0.5 font-medium">Personal AI Coding Engineer</p>
        </div>
        <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] px-2 py-0.5 rounded font-mono font-semibold">
          v0.7.0
        </span>
      </div>

      {/* New Task Action */}
      <button
        onClick={onNewTask}
        className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium text-xs py-2.5 px-3 rounded-lg shadow-md transition-all flex items-center justify-center gap-2 mb-4"
      >
        <span className="text-sm font-bold">+</span>
        <span>New Agent Task</span>
      </button>

      {/* Recent Tasks List */}
      <div className="flex-1 overflow-y-auto space-y-1 mb-4 pr-1">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-2 mb-1.5">
          Recent Tasks
        </div>

        {tasks.length === 0 ? (
          <div className="text-[11px] text-slate-500 px-2 py-3 italic text-center border border-dashed border-slate-800 rounded-lg">
            No agent tasks yet.
          </div>
        ) : (
          tasks.map((task) => (
            <button
              key={task.id}
              onClick={() => onSelectTask(task.id)}
              className={`w-full text-left px-2.5 py-2 rounded-lg text-xs font-medium transition-all flex flex-col gap-1 border ${
                activeTaskId === task.id
                  ? "bg-slate-900 border-blue-500/50 text-slate-100 shadow-sm"
                  : "bg-transparent border-transparent text-slate-400 hover:bg-slate-900/60 hover:text-slate-200"
              }`}
            >
              <div className="flex justify-between items-center w-full">
                <span className="truncate max-w-[170px] font-semibold">{task.title}</span>
                <span
                  className={`w-2 h-2 rounded-full shrink-0 ${
                    task.status === "completed"
                      ? "bg-emerald-400"
                      : task.status === "error"
                      ? "bg-rose-500"
                      : "bg-blue-400 animate-pulse"
                  }`}
                />
              </div>
              <span className="text-[10px] text-slate-500 font-mono">
                {task.createdAt.slice(11, 16)}
              </span>
            </button>
          ))
        )}
      </div>

      {/* Workspace File Explorer */}
      <div className="h-44 mb-4">
        <FileTreeExplorer />
      </div>

      {/* User Authentication & Settings Footer */}
      <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between">
        <AuthWidget />
      </div>
    </aside>
  );
}
