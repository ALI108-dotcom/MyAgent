"use client";

import { useEffect, useState } from "react";
import { ChatSidebar } from "@/components/ChatSidebar";
import { DiffViewerModal } from "@/components/DiffViewerModal";
import { MessageComposer } from "@/components/MessageComposer";
import { MessageList } from "@/components/MessageList";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import {
  addSessionMessage,
  cancelAgentTask,
  createSession,
  fetchSessions,
  streamAgentGoal,
} from "@/lib/api";
import { AgentEventMessage, FileChangeItem } from "@/types/agent";
import { ChatMessage, ChatSession } from "@/types/chat";

export function ConversationalLayout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(true);
  const [activeWorkspace, setActiveWorkspace] = useState<string>("AgentAI/backend");
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isWorking, setIsWorking] = useState<boolean>(false);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);

  const [diffModalFile, setDiffModalFile] = useState<FileChangeItem | null>(null);

  useEffect(() => {
    loadBackendSessions();
  }, []);

  async function loadBackendSessions() {
    try {
      const backendSessions = await fetchSessions();
      const mapped: ChatSession[] = backendSessions.map((s) => ({
        id: s.session_id,
        title: s.title,
        createdAt: s.created_at,
        updatedAt: s.updated_at,
        workspace: "AgentAI/backend",
        messages: s.messages.map((m, idx) => ({
          id: `msg-${s.session_id}-${idx}`,
          role: m.role === "user" ? "user" : "assistant",
          content: m.content,
          timestamp: m.timestamp,
        })),
      }));
      setSessions(mapped);
    } catch {
      // Local fallback if unauthenticated or offline
    }
  }

  function handleNewChat() {
    setActiveSessionId(null);
    setMessages([]);
    setIsWorking(false);
    setActiveTaskId(null);
  }

  function handleSelectSession(id: string) {
    const session = sessions.find((s) => s.id === id);
    if (!session) return;
    setActiveSessionId(session.id);
    setMessages(session.messages);
    setIsWorking(false);
  }

  function handleDeleteSession(id: string) {
    setSessions((prev) => prev.filter((s) => s.id !== id));
    if (activeSessionId === id) {
      handleNewChat();
    }
  }

  async function handleSendMessage(promptText: string) {
    if (!promptText.trim() || isWorking) return;

    const nowIso = new Date().toISOString();
    const taskId = `task-${Date.now()}`;
    setActiveTaskId(taskId);
    setIsWorking(true);

    let currentSessionId = activeSessionId;
    if (!currentSessionId) {
      currentSessionId = `sess-${Date.now()}`;
      const newSession: ChatSession = {
        id: currentSessionId,
        title: promptText.slice(0, 30) + (promptText.length > 30 ? "..." : ""),
        createdAt: nowIso,
        updatedAt: nowIso,
        workspace: activeWorkspace,
        messages: [],
      };
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(currentSessionId);

      try {
        await createSession({ title: newSession.title });
      } catch {
        // Backend fallback
      }
    }

    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      role: "user",
      content: promptText,
      timestamp: nowIso,
    };

    setMessages((prev) => {
      const lastMsg = prev[prev.length - 1];
      if (lastMsg && lastMsg.role === "user" && lastMsg.content.trim() === promptText.trim()) {
        return prev;
      }
      return [...prev, userMsg];
    });

    try {
      await addSessionMessage(currentSessionId, {
        role: "user",
        content: promptText,
      });
    } catch {
      // Fallback
    }

    let currentFileChanges: FileChangeItem[] = [];

    await streamAgentGoal(
      { goal: promptText, provider: "mock" },
      (event: AgentEventMessage) => {
        handleAgentEvent(event, (fileChange) => {
          currentFileChanges = [...currentFileChanges, fileChange];
        });
      },
      (error: Error) => {
        setIsWorking(false);
        const errTile: ChatMessage = {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: `⚠️ Error processing request: ${error.message}`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errTile]);
      }
    );
  }

  function handleAgentEvent(
    event: AgentEventMessage,
    onFileChange: (fc: FileChangeItem) => void
  ) {
    const nowIso = new Date().toISOString();

    switch (event.event_type) {
      case "agent.started":
      case "agent.thinking":
      case "agent.planning":
        setIsWorking(true);
        break;

      case "agent.tool.started":
        const tName = String(event.data.tool_name || "tool");
        const toolMsg: ChatMessage = {
          id: `tool-${Date.now()}-${Math.random()}`,
          role: "tool",
          content: String(event.data.thought || `Executing ${tName}...`),
          toolName: tName,
          timestamp: nowIso,
        };
        setMessages((prev) => [...prev, toolMsg]);
        break;

      case "agent.tool.completed":
        if (event.data.output) {
          setMessages((prev) => {
            const updated = [...prev];
            const lastTool = updated.reverse().find((m) => m.role === "tool" && !m.toolOutput);
            if (lastTool) {
              lastTool.toolOutput = String(event.data.output);
            }
            return [...prev];
          });
        }
        break;

      case "agent.file.changed":
        const fcItem: FileChangeItem = {
          file_path: String(event.data.file_path || "file"),
          change_type: (event.data.change_type as "added" | "modified" | "deleted") || "modified",
          snippet: event.data.snippet ? String(event.data.snippet) : undefined,
        };
        onFileChange(fcItem);
        break;

      case "agent.test.completed":
        setMessages((prev) => {
          const updated = [...prev];
          const lastAssistant = updated.reverse().find((m) => m.role === "assistant");
          if (lastAssistant) {
            lastAssistant.testResults = {
              total_tests: Number(event.data.total_tests || 0),
              passed: Number(event.data.passed || 0),
              failed: Number(event.data.failed || 0),
              output: String(event.data.output || ""),
            };
          }
          return [...prev];
        });
        break;

      case "agent.completed":
        setIsWorking(false);
        if (event.data.final_answer) {
          const finalAnsStr = String(event.data.final_answer);
          const ansMsg: ChatMessage = {
            id: `ans-${Date.now()}`,
            role: "assistant",
            content: finalAnsStr,
            timestamp: nowIso,
          };
          setMessages((prev) => [...prev, ansMsg]);
        }
        break;

      case "agent.error":
        setIsWorking(false);
        const errMsg: ChatMessage = {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: `❌ Task Error: ${String(event.data.error)}`,
          timestamp: nowIso,
        };
        setMessages((prev) => [...prev, errMsg]);
        break;
    }
  }

  async function handleStop() {
    if (activeTaskId) {
      try {
        await cancelAgentTask(activeTaskId);
        setIsWorking(false);
      } catch (e) {
        console.error("Failed to stop agent:", e);
      }
    }
  }

  function handleOpenDiff(filePath: string, snippet?: string) {
    setDiffModalFile({
      file_path: filePath,
      change_type: "modified",
      snippet: snippet,
    });
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      {/* ChatGPT Style Left Sidebar */}
      <ChatSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
        isOpen={isSidebarOpen}
        onToggleOpen={() => setIsSidebarOpen((prev) => !prev)}
        activeWorkspace={activeWorkspace}
        onSelectWorkspace={(ws) => setActiveWorkspace(ws)}
      />

      {/* Main Conversational Container */}
      <div className="flex-1 flex flex-col h-screen bg-slate-950 overflow-hidden relative">
        {/* Top Header Bar */}
        <div className="px-6 py-3 border-b border-slate-800/80 bg-slate-950/80 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            {!isSidebarOpen && (
              <button
                onClick={() => setIsSidebarOpen(true)}
                className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-900 transition-colors text-sm"
              >
                ▶
              </button>
            )}
            <span className="font-extrabold text-sm text-slate-200">MyAgent Conversational AI</span>
            <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] px-2 py-0.5 rounded font-mono font-semibold">
              Online
            </span>
          </div>

          <button
            onClick={handleNewChat}
            className="text-xs bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 px-3 py-1 rounded-lg transition-colors font-medium"
          >
            + New Chat
          </button>
        </div>

        {/* Center Viewport: Welcome Screen OR Message Stream */}
        {messages.length === 0 ? (
          <WelcomeScreen onSelectPrompt={handleSendMessage} />
        ) : (
          <MessageList messages={messages} onOpenDiff={handleOpenDiff} />
        )}

        {/* Floating Message Composer Bar */}
        <MessageComposer
          onSendMessage={handleSendMessage}
          onStop={handleStop}
          isWorking={isWorking}
          activeWorkspace={activeWorkspace}
        />
      </div>

      {/* Code Diff Preview Modal */}
      <DiffViewerModal
        fileChange={diffModalFile}
        onClose={() => setDiffModalFile(null)}
      />
    </div>
  );
}
