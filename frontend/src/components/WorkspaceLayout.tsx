"use client";

import { useState } from "react";
import { AgentChat } from "@/components/AgentChat";
import { AgentPanel } from "@/components/AgentPanel";
import { Sidebar } from "@/components/Sidebar";
import { approveAgentTask, cancelAgentTask, streamAgentGoal } from "@/lib/api";
import { AgentEventMessage, AgentStatus, FileChangeItem, TaskRecord, TestResultItem } from "@/types/agent";

interface ChatMessage {
  id: string;
  role: "user" | "agent" | "system" | "tool";
  content: string;
  toolName?: string;
  toolOutput?: string;
  timestamp: string;
}

export function WorkspaceLayout() {
  const [tasks, setTasks] = useState<TaskRecord[]>([]);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);

  const [agentStatus, setAgentStatus] = useState<AgentStatus>("ready");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [plan, setPlan] = useState<string[]>([]);
  const [fileChanges, setFileChanges] = useState<FileChangeItem[]>([]);
  const [testResults, setTestResults] = useState<TestResultItem | null>(null);
  const [pendingApproval, setPendingApproval] = useState<{ taskId: string; action: string } | null>(null);

  function handleNewTask() {
    setActiveTaskId(null);
    setMessages([]);
    setPlan([]);
    setFileChanges([]);
    setTestResults(null);
    setAgentStatus("ready");
    setPendingApproval(null);
  }

  function handleSelectTask(taskId: string) {
    const task = tasks.find((t) => t.id === taskId);
    if (!task) return;
    setActiveTaskId(task.id);
    setAgentStatus(task.status);
    setPlan(task.plan);
    setFileChanges(task.fileChanges);
    setTestResults(task.testResults);
    setMessages([
      {
        id: `m-goal-${task.id}`,
        role: "user",
        content: task.goal,
        timestamp: task.createdAt,
      },
      ...(task.finalAnswer
        ? [
            {
              id: `m-ans-${task.id}`,
              role: "agent" as const,
              content: task.finalAnswer,
              timestamp: task.createdAt,
            },
          ]
        : []),
    ]);
  }

  async function handleSendMessage(goal: string) {
    const taskId = `task-${Date.now()}`;
    const nowIso = new Date().toISOString();

    const newRecord: TaskRecord = {
      id: taskId,
      title: goal.slice(0, 30) + (goal.length > 30 ? "..." : ""),
      goal: goal,
      status: "thinking",
      createdAt: nowIso,
      plan: [],
      fileChanges: [],
      testResults: null,
    };

    setTasks((prev) => [newRecord, ...prev]);
    setActiveTaskId(taskId);
    setAgentStatus("thinking");
    setPlan([]);
    setFileChanges([]);
    setTestResults(null);
    setPendingApproval(null);

    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      role: "user",
      content: goal,
      timestamp: nowIso,
    };
    setMessages((prev) => [...prev, userMsg]);

    await streamAgentGoal(
      { goal, provider: "mock" },
      (event: AgentEventMessage) => {
        handleAgentEvent(taskId, event);
      },
      (error: Error) => {
        setAgentStatus("error");
        const errTile: ChatMessage = {
          id: `err-${Date.now()}`,
          role: "agent",
          content: `⚠️ Error executing agent task: ${error.message}`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errTile]);
      }
    );
  }

  function handleAgentEvent(taskId: string, event: AgentEventMessage) {
    const nowIso = new Date().toISOString();

    switch (event.event_type) {
      case "agent.started":
        setAgentStatus("thinking");
        break;

      case "agent.thinking":
        setAgentStatus("thinking");
        break;

      case "agent.planning":
        setAgentStatus("planning");
        if (event.data.plan && Array.isArray(event.data.plan)) {
          setPlan(event.data.plan as string[]);
        }
        break;

      case "agent.tool.started":
        const tName = String(event.data.tool_name || "tool");
        if (tName === "write_file" || tName === "edit_file") {
          setAgentStatus("editing_files");
        } else if (tName === "run_command") {
          setAgentStatus("running_command");
        } else {
          setAgentStatus("inspecting");
        }

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
        setFileChanges((prev) => [
          ...prev,
          {
            file_path: String(event.data.file_path || "file"),
            change_type: (event.data.change_type as "added" | "modified" | "deleted") || "modified",
            snippet: event.data.snippet ? String(event.data.snippet) : undefined,
          },
        ]);
        break;

      case "agent.test.started":
        setAgentStatus("running_tests");
        break;

      case "agent.test.completed":
        setTestResults({
          total_tests: Number(event.data.total_tests || 0),
          passed: Number(event.data.passed || 0),
          failed: Number(event.data.failed || 0),
          output: String(event.data.output || ""),
        });
        break;

      case "agent.approval_required":
        setAgentStatus("approval_required");
        setPendingApproval({ taskId, action: String(event.data.action || "Dangerous operation") });
        break;

      case "agent.completed":
        setAgentStatus("completed");
        if (event.data.final_answer) {
          const finalAnsStr = String(event.data.final_answer);
          const ansMsg: ChatMessage = {
            id: `ans-${Date.now()}`,
            role: "agent",
            content: finalAnsStr,
            timestamp: nowIso,
          };
          setMessages((prev) => [...prev, ansMsg]);

          setTasks((prev) =>
            prev.map((t) =>
              t.id === taskId
                ? { ...t, status: "completed", finalAnswer: finalAnsStr }
                : t
            )
          );
        }
        break;

      case "agent.error":
        setAgentStatus("error");
        const errMsg: ChatMessage = {
          id: `err-${Date.now()}`,
          role: "agent",
          content: `❌ Task Error: ${String(event.data.error)}`,
          timestamp: nowIso,
        };
        setMessages((prev) => [...prev, errMsg]);
        break;
    }
  }

  async function handleStopAgent() {
    if (activeTaskId) {
      try {
        await cancelAgentTask(activeTaskId);
        setAgentStatus("error");
      } catch (e) {
        console.error("Failed to cancel task:", e);
      }
    }
  }

  async function handleApprove(approved: boolean) {
    if (pendingApproval) {
      try {
        await approveAgentTask(pendingApproval.taskId, approved);
        setPendingApproval(null);
        setAgentStatus("thinking");
      } catch (e) {
        console.error("Failed to submit approval:", e);
      }
    }
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      <Sidebar
        tasks={tasks}
        activeTaskId={activeTaskId}
        onSelectTask={handleSelectTask}
        onNewTask={handleNewTask}
      />
      <AgentChat
        messages={messages}
        status={agentStatus}
        onSendMessage={handleSendMessage}
        onStopAgent={handleStopAgent}
      />
      <AgentPanel
        status={agentStatus}
        plan={plan}
        fileChanges={fileChanges}
        testResults={testResults}
        pendingApproval={pendingApproval}
        onApprove={handleApprove}
      />
    </div>
  );
}
