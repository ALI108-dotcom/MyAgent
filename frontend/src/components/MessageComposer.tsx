"use client";

import { useRef, useState } from "react";

interface MessageComposerProps {
  onSendMessage: (content: string) => void;
  onStop: () => void;
  isWorking: boolean;
  activeWorkspace: string;
}

export function MessageComposer({
  onSendMessage,
  onStop,
  isWorking,
  activeWorkspace,
}: MessageComposerProps) {
  const [input, setInput] = useState<string>("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleSubmit(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!input.trim() || isWorking) return;
    onSendMessage(input.trim());
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  function handleInputChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }

  return (
    <div className="p-4 bg-gradient-to-t from-slate-950 via-slate-950/90 to-transparent shrink-0">
      <div className="max-w-3xl mx-auto bg-slate-900/90 border border-slate-800 rounded-2xl p-2.5 shadow-2xl backdrop-blur-md focus-within:border-blue-500/70 transition-all">
        {/* Active Context Pill & Attachments Row */}
        <div className="flex items-center justify-between px-2 pb-1.5 border-b border-slate-800/50 mb-1 text-[11px] text-slate-400">
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="hover:text-slate-200 transition-colors flex items-center gap-1 font-mono text-[10px] bg-slate-800/80 px-2 py-0.5 rounded-md border border-slate-700/60"
            >
              <span className="text-blue-400">📁</span>
              <span>Working in:</span>
              <span className="text-slate-200 font-semibold">{activeWorkspace}</span>
            </button>
          </div>

          <span className="text-[10px] text-slate-500 font-mono hidden sm:inline">
            Shift+Enter for newline
          </span>
        </div>

        {/* Main Textarea Input */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          disabled={isWorking}
          placeholder={
            isWorking
              ? "MyAgent is working on your request... Click Stop to cancel."
              : "Message MyAgent..."
          }
          rows={1}
          className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 px-2 py-1 focus:outline-none resize-none disabled:opacity-50 min-h-[36px]"
        />

        {/* Action Toolbar */}
        <div className="flex justify-between items-center pt-1 px-1">
          <div className="flex items-center gap-1">
            {/* Attachment Button */}
            <button
              type="button"
              title="Attach File"
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 rounded-lg transition-colors text-sm"
            >
              📎
            </button>
            {/* Voice Mic Placeholder Button */}
            <button
              type="button"
              title="Voice Input"
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 rounded-lg transition-colors text-sm"
            >
              🎙️
            </button>
          </div>

          <div>
            {isWorking ? (
              <button
                type="button"
                onClick={onStop}
                className="bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs px-3.5 py-1.5 rounded-xl transition-all shadow-md flex items-center gap-1.5 animate-pulse"
              >
                <span>⏹</span>
                <span>Stop</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={() => handleSubmit()}
                disabled={!input.trim()}
                className="bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs p-2 rounded-xl transition-all shadow-md disabled:opacity-30 disabled:hover:bg-blue-600 flex items-center justify-center w-8 h-8"
              >
                ↑
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
