"use client";

import { useEffect, useRef, useState } from "react";
import { AgentStatus } from "@/types/agent";

interface ChatMessage {
  id: string;
  role: "user" | "agent" | "system" | "tool";
  content: string;
  toolName?: string;
  toolOutput?: string;
  timestamp: string;
}

interface AgentChatProps {
  messages: ChatMessage[];
  status: AgentStatus;
  onSendMessage: (goal: string) => void;
  onStopAgent: () => void;
}

export function AgentChat({ messages, status, onSendMessage, onStopAgent }: AgentChatProps) {
  const [input, setInput] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const isAgentActive = status !== "ready" && status !== "completed" && status !== "error";

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, status]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || isAgentActive) return;
    onSendMessage(input.trim());
    setInput("");
  }

  function handleQuickPrompt(promptText: string) {
    if (isAgentActive) return;
    onSendMessage(promptText);
  }

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-900 border-r border-slate-800/80 overflow-hidden">
      {/* Top Banner Bar */}
      <div className="bg-slate-950/80 border-b border-slate-800/80 px-6 py-3.5 flex justify-between items-center shrink-0">
        <div>
          <h2 className="font-extrabold text-sm text-slate-100 flex items-center gap-2">
            ALI Software Engineer Workspace
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Active Workspace: <code className="text-blue-400 font-mono">AgentAI/backend</code>
          </p>
        </div>

        {isAgentActive && (
          <button
            onClick={onStopAgent}
            className="bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs px-3.5 py-1.5 rounded-lg shadow-md transition-all animate-pulse"
          >
            ⏹ STOP AGENT
          </button>
        )}
      </div>

      {/* Conversation Stream Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="max-w-2xl mx-auto my-12 text-center space-y-6">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 via-teal-500 to-indigo-600 flex items-center justify-center font-extrabold text-2xl text-white mx-auto shadow-xl">
              A
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-100">Welcome to ALI Agent Workspace</h3>
              <p className="text-slate-400 text-sm mt-1">
                Your personal autonomous software engineer. Simply describe your task.
              </p>
            </div>

            {/* Quick Action Chips */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg mx-auto pt-2 text-left">
              <button
                onClick={() =>
                  handleQuickPrompt(
                    "Create a small Python calculator module with add, subtract, multiply and divide functions. Create tests for it, run the tests, and explain what you created."
                  )
                }
                className="bg-slate-950 hover:bg-slate-800 border border-slate-800 p-3 rounded-xl transition-all group"
              >
                <div className="text-xs font-bold text-blue-400 group-hover:text-blue-300">
                  🧮 Build Calculator & Run Tests
                </div>
                <div className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                  Creates calculator.py, test suite, executes Pytest, and synthesizes report.
                </div>
              </button>

              <button
                onClick={() => handleQuickPrompt("Inspect the backend main.py architecture.")}
                className="bg-slate-950 hover:bg-slate-800 border border-slate-800 p-3 rounded-xl transition-all group"
              >
                <div className="text-xs font-bold text-emerald-400 group-hover:text-emerald-300">
                  🔍 Inspect Project Architecture
                </div>
                <div className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                  Scans workspace tree and performs static AST analysis.
                </div>
              </button>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className="max-w-3xl mx-auto">
              {msg.role === "user" ? (
                <div className="flex justify-end mb-4">
                  <div className="bg-blue-600 text-white rounded-2xl rounded-tr-none px-4 py-3 text-sm shadow-md max-w-lg">
                    {msg.content}
                  </div>
                </div>
              ) : msg.role === "tool" ? (
                <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3 mb-4 font-mono text-xs shadow-sm">
                  <div className="flex items-center justify-between text-slate-400 pb-1.5 border-b border-slate-800/60 mb-2">
                    <span className="flex items-center gap-2 font-bold text-blue-400">
                      🔧 {msg.toolName}
                    </span>
                    <span className="text-[10px] text-slate-500">{msg.timestamp.slice(11, 19)}</span>
                  </div>
                  <div className="text-slate-300 text-xs mb-2">{msg.content}</div>
                  {msg.toolOutput && (
                    <pre className="bg-slate-900 p-2.5 rounded-lg border border-slate-800 text-slate-400 text-[11px] overflow-x-auto whitespace-pre-wrap max-h-40">
                      {msg.toolOutput}
                    </pre>
                  )}
                </div>
              ) : (
                <div className="bg-slate-950/90 border border-slate-800 rounded-2xl rounded-tl-none p-5 mb-4 shadow-lg text-sm text-slate-200 leading-relaxed">
                  <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 mb-2 pb-1 border-b border-slate-800/60">
                    <span>⚡ ALI Agent Response</span>
                  </div>
                  <div className="whitespace-pre-wrap font-sans">{msg.content}</div>
                </div>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Bottom Coding Input Bar */}
      <form onSubmit={handleSubmit} className="p-4 bg-slate-950 border-t border-slate-800/80 shrink-0">
        <div className="max-w-3xl mx-auto bg-slate-900 border border-slate-800 rounded-2xl p-2 shadow-xl focus-within:border-blue-500/70 transition-all">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isAgentActive}
            placeholder={
              isAgentActive
                ? "ALI is working on the task... Click STOP AGENT to cancel."
                : "Ask ALI to build a module, find bugs, run tests, or refactor code..."
            }
            rows={2}
            className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 p-2 focus:outline-none resize-none disabled:opacity-50"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />

          <div className="flex justify-between items-center pt-2 px-2 border-t border-slate-800/60">
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono text-[10px]">
                Workspace: backend
              </span>
              <span>Press Shift+Enter for new line</span>
            </div>

            <div className="flex items-center gap-2">
              {isAgentActive ? (
                <button
                  type="button"
                  onClick={onStopAgent}
                  className="bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs px-4 py-1.5 rounded-lg transition-colors shadow-sm"
                >
                  Stop
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!input.trim()}
                  className="bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs px-4 py-1.5 rounded-lg transition-colors shadow-md disabled:opacity-40"
                >
                  Send Task →
                </button>
              )}
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
