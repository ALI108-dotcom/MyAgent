export interface LLMRequest {
  prompt: string;
  system_prompt?: string;
  provider?: "mock" | "gemini" | "openai";
  model?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface LLMResponse {
  content: string;
  provider: string;
  model: string;
  finish_reason: string;
  usage: TokenUsage;
  timestamp: string;
}
