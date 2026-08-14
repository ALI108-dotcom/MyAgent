export type AgentStatus =
  | "ready"
  | "thinking"
  | "planning"
  | "inspecting"
  | "reading_files"
  | "editing_files"
  | "running_command"
  | "running_tests"
  | "error"
  | "completed"
  | "approval_required";

export type AgentEventType =
  | "agent.started"
  | "agent.thinking"
  | "agent.planning"
  | "agent.tool.started"
  | "agent.tool.completed"
  | "agent.file.changed"
  | "agent.test.started"
  | "agent.test.completed"
  | "agent.approval_required"
  | "agent.completed"
  | "agent.error";

export interface FileChangeItem {
  file_path: string;
  change_type: "added" | "modified" | "deleted";
  snippet?: string;
}

export interface TestResultItem {
  total_tests: number;
  passed: number;
  failed: number;
  output: string;
}

export interface AgentEventMessage {
  event_id: string;
  task_id: string;
  event_type: AgentEventType;
  timestamp: string;
  data: Record<string, unknown>;
}

export interface TaskRecord {
  id: string;
  title: string;
  goal: string;
  status: AgentStatus;
  createdAt: string;
  plan: string[];
  fileChanges: FileChangeItem[];
  testResults: TestResultItem | null;
  finalAnswer?: string;
}
