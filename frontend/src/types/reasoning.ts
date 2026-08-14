export interface AgentPlanStep {
  step_number: number;
  thought: string;
  tool_name?: string | null;
  tool_params?: Record<string, unknown> | null;
  status: "pending" | "executing" | "completed" | "failed";
  observation?: string | null;
}

export interface ReasoningRequest {
  goal: string;
  context?: string;
  max_iterations?: number;
  provider?: "mock" | "gemini" | "openai";
  model?: string;
}

export interface ReasoningResponse {
  goal: string;
  final_answer: string;
  trajectory: AgentPlanStep[];
  total_iterations: number;
  execution_time_ms: number;
  timestamp: string;
}
