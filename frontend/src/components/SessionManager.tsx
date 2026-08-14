"use client";

import { useCallback, useEffect, useState } from "react";
import {
  fetchSessions,
  createSession,
  fetchProjectContext,
  addSessionMessage,
} from "@/lib/api";
import { ProjectContext, SessionMemory } from "@/types/memory";

export function SessionManager() {
  const [sessions, setSessions] = useState<SessionMemory[]>([]);
  const [selectedSession, setSelectedSession] = useState<SessionMemory | null>(null);
  const [context, setContext] = useState<ProjectContext | null>(null);
  const [newTitle, setNewTitle] = useState<string>("");
  const [newMessage, setNewMessage] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [creating, setCreating] = useState<boolean>(false);
  const [sending, setSending] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [sessionsData, contextData] = await Promise.all([
        fetchSessions(),
        fetchProjectContext(),
      ]);
      setSessions(sessionsData);
      setContext(contextData);
      if (sessionsData.length > 0 && !selectedSession) {
        setSelectedSession(sessionsData[0]);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load memory data";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [selectedSession]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      const created = await createSession({
        title: newTitle.trim() || undefined,
        initial_system_prompt: "You are ALI, a personal AI Software Engineer Agent.",
      });
      setSessions((prev) => [created, ...prev]);
      setSelectedSession(created);
      setNewTitle("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create session";
      setError(msg);
    } finally {
      setCreating(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSession || !newMessage.trim()) return;

    setSending(true);
    setError(null);
    try {
      const updated = await addSessionMessage(selectedSession.session_id, {
        role: "user",
        content: newMessage,
      });
      setSelectedSession(updated);
      setSessions((prev) =>
        prev.map((s) => (s.session_id === updated.session_id ? updated : s))
      );
      setNewMessage("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to send message";
      setError(msg);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-2">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <span>💾</span> Persistent Memory &amp; Project Context
          </h2>
          <p className="text-slate-400 text-xs mt-1">
            MongoDB session persistence (<code className="text-blue-400 font-mono">db.sessions</code>) &amp; live workspace project context builder.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="text-xs px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono rounded-lg transition-all border border-slate-700 disabled:opacity-50"
        >
          {loading ? "Refreshing..." : "Reload Memory & Context"}
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs font-mono">
          <div className="font-bold mb-1">⚠️ Memory Error:</div>
          <div>{error}</div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Workspace Project Context Summary */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3 font-mono text-xs">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800">
              <span className="font-bold text-teal-400 uppercase tracking-wider">
                Workspace Project Context
              </span>
              <span className="text-slate-500 text-[10px]">
                {context ? `${context.file_count} files` : "Scanning..."}
              </span>
            </div>

            {context ? (
              <>
                <div>
                  <span className="text-slate-500 font-bold">Root: </span>
                  <span className="text-slate-300 text-[11px] truncate block">{context.workspace_root}</span>
                </div>

                <div>
                  <span className="text-slate-500 font-bold">Key Entry Files ({context.key_files.length}):</span>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {context.key_files.map((file) => (
                      <span
                        key={file}
                        className="bg-slate-900 border border-slate-800 text-blue-400 text-[10px] px-2 py-0.5 rounded"
                      >
                        {file}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <span className="text-slate-500 font-bold">File Tree Summary:</span>
                  <pre className="mt-1.5 p-3 bg-slate-900/90 border border-slate-800 rounded-lg text-slate-300 text-[11px] whitespace-pre-wrap max-h-48 overflow-y-auto leading-relaxed">
                    {context.structure_summary}
                  </pre>
                </div>
              </>
            ) : (
              <div className="text-slate-500 py-4 text-center">Scanning workspace tree...</div>
            )}
          </div>
        </div>

        {/* Sessions & Chat History Manager */}
        <div className="lg:col-span-7 space-y-4">
          {/* Create Session Form */}
          <form onSubmit={handleCreateSession} className="flex gap-2">
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="New session title (e.g. Debugging MongoDB)..."
              className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-blue-500"
            />
            <button
              type="submit"
              disabled={creating}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-mono text-xs font-bold rounded-lg transition-all shadow-md disabled:opacity-50"
            >
              {creating ? "Creating..." : "+ New Session"}
            </button>
          </form>

          {/* Session Selector & Messages */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-4 font-mono text-xs">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-800">
              <span className="font-bold text-indigo-400 uppercase tracking-wider">
                Sessions ({sessions.length})
              </span>

              {sessions.length > 0 && (
                <select
                  value={selectedSession?.session_id || ""}
                  onChange={(e) => {
                    const found = sessions.find((s) => s.session_id === e.target.value);
                    if (found) setSelectedSession(found);
                  }}
                  className="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded px-2 py-1 font-mono focus:outline-none"
                >
                  {sessions.map((s) => (
                    <option key={s.session_id} value={s.session_id}>
                      {s.title} ({s.messages.length} msgs)
                    </option>
                  ))}
                </select>
              )}
            </div>

            {selectedSession ? (
              <div className="space-y-3">
                <div className="text-slate-400 text-[11px] flex justify-between">
                  <span>ID: <code className="text-blue-400">{selectedSession.session_id}</code></span>
                  <span>Updated: {new Date(selectedSession.updated_at).toLocaleTimeString()}</span>
                </div>

                {/* Messages List */}
                <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                  {selectedSession.messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg border text-xs leading-relaxed ${
                        msg.role === "user"
                          ? "bg-blue-950/40 border-blue-800/40 text-blue-200 ml-4"
                          : msg.role === "assistant"
                          ? "bg-slate-900 border-slate-800 text-slate-200 mr-4"
                          : "bg-slate-900/40 border-slate-800/40 text-slate-400 italic text-[11px]"
                      }`}
                    >
                      <div className="flex justify-between items-center mb-1 text-[10px] opacity-70">
                        <span className="font-bold uppercase">{msg.role}</span>
                        <span>{new Date(msg.timestamp).toLocaleTimeString()}</span>
                      </div>
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                    </div>
                  ))}
                </div>

                {/* Append Message Input */}
                <form onSubmit={handleSendMessage} className="flex gap-2 pt-2">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Append message to session history..."
                    className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-blue-500"
                    required
                  />
                  <button
                    type="submit"
                    disabled={sending || !newMessage.trim()}
                    className="px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg transition-all disabled:opacity-50"
                  >
                    {sending ? "..." : "Send"}
                  </button>
                </form>
              </div>
            ) : (
              <div className="text-slate-500 py-6 text-center">No active session selected.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
