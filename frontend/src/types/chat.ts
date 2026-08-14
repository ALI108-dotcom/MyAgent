import { FileChangeItem, TestResultItem } from "@/types/agent";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "tool";
  content: string;
  timestamp: string;
  toolName?: string;
  toolOutput?: string;
  fileChanges?: FileChangeItem[];
  testResults?: TestResultItem | null;
  status?: "thinking" | "planning" | "executing" | "completed" | "error";
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  workspace: string;
  messages: ChatMessage[];
}
