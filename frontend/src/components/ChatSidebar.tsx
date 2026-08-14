"use client";

import { useState } from "react";
import { AuthWidget } from "@/components/AuthWidget";
import { ChatSession } from "@/types/chat";

interface ChatSidebarProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string) => void;
  isOpen: boolean;
  onToggleOpen: () => void;
  activeWorkspace: string;
  onSelectWorkspace: (ws: string) => void;
}

export function ChatSidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  isOpen,
  onToggleOpen,
  activeWorkspace,
  onSelectWorkspace,
}: ChatSidebarProps) {
  const [searchQuery, setSearchQuery] = useState<string>("");

  const filteredSessions = sessions.filter((s) =>
    s.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <>
      {/* Sidebar Overlay on Mobile */}
      {isOpen && (
        <div
          onClick={onToggleOpen}
          className="md:hidden fixed inset-0 z-30 bg-slate-950/80 backdrop-blur-sm"
        />
      )}

      {/* Main Sidebar Container */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-40 bg-slate-950 border-r border-slate-800/80 flex flex-col transition-all duration-300 ease-in-out select-none shrink-0 ${
          isOpen ? "w-64" : "w-0 md:w-16"
        } overflow-hidden`}
      >
        {/* Top Header */}
        <div className="p-3.5 border-b border-slate-800/80 flex items-center justify-between">
          <div className={`flex items-center gap-2.5 ${!isOpen && "hidden md:flex"}`}>
            <div className="w-7 h-7 rounded-xl bg-gradient-to-tr from-blue-600 via-teal-500 to-indigo-600 flex items-center justify-center font-black text-white text-xs shadow-md">
              M
            </div>
            {isOpen && (
              <span className="font-extrabold text-sm tracking-tight bg-gradient-to-r from-blue-400 to-teal-300 bg-clip-text text-transparent">
                MyAgent
              </span>
            )}
          </div>

          <button
            onClick={onToggleOpen}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-900 transition-colors"
            title="Toggle Sidebar"
          >
            {isOpen ? "◀" : "▶"}
          </button>
        </div>

        {isOpen && (
          <div className="p-3 space-y-3 flex-1 overflow-y-auto">
            {/* New Chat Button */}
            <button
              onClick={onNewChat}
              className="w-full bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-100 font-medium text-xs py-2.5 px-3 rounded-xl transition-all flex items-center justify-between shadow-sm group"
            >
              <div className="flex items-center gap-2">
                <span className="text-blue-400 font-bold text-sm">+</span>
                <span>New Chat</span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono group-hover:text-slate-400">
                ⌘K
              </span>
            </button>

            {/* Search Input */}
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search chats..."
                className="w-full bg-slate-900/60 border border-slate-800/80 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/60"
              />
            </div>

            {/* Workspace Selector */}
            <div className="pt-1">
              <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">
                Workspace
              </label>
              <select
                value={activeWorkspace}
                onChange={(e) => onSelectWorkspace(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 text-slate-200 text-xs rounded-lg px-2 py-1.5 focus:outline-none"
              >
                <option value="AgentAI/backend">AgentAI / backend</option>
                <option value="AgentAI/frontend">AgentAI / frontend</option>
                <option value="AgentAI/root">AgentAI / root</option>
              </select>
            </div>

            {/* Conversation History List */}
            <div className="space-y-3 pt-2">
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                Recent Chats
              </div>

              {filteredSessions.length === 0 ? (
                <div className="text-[11px] text-slate-500 italic py-3 text-center border border-dashed border-slate-800 rounded-lg">
                  No conversations saved yet.
                </div>
              ) : (
                <div className="space-y-1">
                  {filteredSessions.map((session) => (
                    <div
                      key={session.id}
                      className={`group flex items-center justify-between px-2.5 py-2 rounded-xl text-xs transition-all cursor-pointer ${
                        activeSessionId === session.id
                          ? "bg-slate-900 border border-slate-800 text-slate-100 font-semibold"
                          : "text-slate-400 hover:bg-slate-900/50 hover:text-slate-200"
                      }`}
                      onClick={() => onSelectSession(session.id)}
                    >
                      <div className="flex items-center gap-2 truncate">
                        <span className="text-slate-500 text-[11px]">💬</span>
                        <span className="truncate">{session.title}</span>
                      </div>

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteSession(session.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-rose-400 text-xs px-1"
                        title="Delete Chat"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Sidebar Footer */}
        {isOpen && (
          <div className="p-3 border-t border-slate-800/80 flex items-center justify-between bg-slate-950">
            <AuthWidget />
          </div>
        )}
      </aside>
    </>
  );
}
