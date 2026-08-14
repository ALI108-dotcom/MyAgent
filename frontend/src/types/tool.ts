export interface ToolParameterSpec {
  type: string;
  description: string;
  required: boolean;
  default?: unknown;
}

export interface ToolDefinition {
  name: string;
  description: string;
  parameters: Record<string, ToolParameterSpec>;
}

export interface ToolExecutionRequest {
  tool_name: string;
  parameters: Record<string, unknown>;
}

export interface ToolResult {
  tool_name: string;
  success: boolean;
  output: string;
  error?: string | null;
  execution_time_ms: number;
  timestamp: string;
}
