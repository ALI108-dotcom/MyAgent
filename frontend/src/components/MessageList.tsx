"use client";

import { useEffect, useRef } from "react";
import { ChatMessage } from "@/types/chat";

interface MessageListProps {
  messages: ChatMessage[];
  onOpenDiff?: (filePath: string, snippet?: string) => void;
}

export function MessageList({ messages, onOpenDiff }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const displayMessages = messages.filter((msg, index) => {
    if (
      index > 0 &&
      msg.role === "user" &&
      messages[index - 1].role === "user" &&
      messages[index - 1].content.trim() === msg.content.trim()
    ) {
      return false;
    }
    return true;
  });

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
      <div className="max-w-3xl mx-auto space-y-6">
        {displayMessages.map((msg) => (
          <div key={msg.id} className="space-y-3">
            {msg.role === "user" ? (
              /* User Prompt Message */
              <div className="flex justify-end">
                <div className="bg-slate-800 text-slate-100 rounded-2xl rounded-tr-none px-4 py-3 text-sm max-w-xl shadow-sm leading-relaxed whitespace-pre-wrap">
                  {msg.content}
                </div>
              </div>
            ) : msg.role === "tool" ? (
              /* Tool Activity Inline Chip */
              <details className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-3 text-xs font-mono shadow-sm group">
                <summary className="cursor-pointer text-slate-300 font-semibold flex items-center justify-between">
                  <span className="flex items-center gap-2 text-blue-400">
                    <span>🔧</span>
                    <span>{msg.toolName || "Agent Action"}</span>
                    <span className="text-slate-400 font-normal">{msg.content}</span>
                  </span>
                  <span className="text-[10px] text-slate-500 group-open:rotate-180 transition-transform">
                    ▼
                  </span>
                </summary>

                {msg.toolOutput && (
                  <div className="mt-2.5 pt-2 border-t border-slate-800/60">
                    <div className="text-[10px] text-slate-500 mb-1">Execution Output:</div>
                    <pre className="bg-slate-900/90 p-3 rounded-lg border border-slate-800 text-[11px] text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-48">
                      {msg.toolOutput}
                    </pre>
                  </div>
                )}
              </details>
            ) : (
              /* Assistant Response Bubble */
              <div className="flex gap-4 items-start">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-teal-400 flex items-center justify-center font-black text-white text-xs shrink-0 shadow-md">
                  M
                </div>
                <div className="flex-1 bg-slate-900/40 border border-slate-800/60 rounded-2xl rounded-tl-none p-5 shadow-sm space-y-4">
                  <div className="prose prose-invert max-w-none text-sm text-slate-200 leading-relaxed font-sans whitespace-pre-wrap">
                    {msg.content}
                  </div>

                  {/* File Modifications Inline List */}
                  {msg.fileChanges && msg.fileChanges.length > 0 && (
                    <div className="pt-3 border-t border-slate-800/60">
                      <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                        Modified Files ({msg.fileChanges.length})
                      </div>
                      <div className="space-y-1.5 font-mono text-xs">
                        {msg.fileChanges.map((file, idx) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800"
                          >
                            <span className="text-slate-300">
                              <span
                                className={`mr-2 font-bold ${
                                  file.change_type === "added"
                                    ? "text-emerald-400"
                                    : file.change_type === "modified"
                                    ? "text-amber-400"
                                    : "text-rose-400"
                                }`}
                              >
                                {file.change_type === "added"
                                  ? "+"
                                  : file.change_type === "modified"
                                  ? "~"
                                  : "-"}
                              </span>
                              {file.file_path}
                            </span>

                            {onOpenDiff && (
                              <button
                                onClick={() => onOpenDiff(file.file_path, file.snippet)}
                                className="text-[10px] text-blue-400 hover:text-blue-300 bg-slate-900 px-2 py-0.5 rounded transition-colors"
                              >
                                View Diff
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Test Results Summary Chip */}
                  {msg.testResults && (
                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 flex items-center justify-between text-xs font-mono">
                      <div className="flex items-center gap-3">
                        <span className="font-bold text-slate-300">Pytest Execution:</span>
                        <span className="text-emerald-400 font-bold">
                          ✓ {msg.testResults.passed} Passed
                        </span>
                        {msg.testResults.failed > 0 && (
                          <span className="text-rose-400 font-bold">
                            ❌ {msg.testResults.failed} Failed
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
