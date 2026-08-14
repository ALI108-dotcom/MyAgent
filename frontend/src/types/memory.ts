export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown> | null;
}

export interface SessionMemory {
  session_id: string;
  title: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
}

export interface CreateSessionRequest {
  title?: string;
  initial_system_prompt?: string;
}

export interface AddMessageRequest {
  role: "user" | "assistant" | "system";
  content: string;
  metadata?: Record<string, unknown>;
}

export interface ProjectContext {
  workspace_root: string;
  file_count: number;
  structure_summary: string;
  key_files: string[];
  timestamp: string;
}
