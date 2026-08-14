import { AgentEventMessage } from "@/types/agent";
import { LoginRequest, RegisterRequest, TokenResponse, User } from "@/types/auth";
import { HealthData } from "@/types/health";
import { LLMRequest, LLMResponse } from "@/types/llm";
import {
  AddMessageRequest,
  CreateSessionRequest,
  ProjectContext,
  SessionMemory,
} from "@/types/memory";
import {
  IndexWorkspaceResponse,
  RAGQueryRequest,
  RAGQueryResponse,
} from "@/types/rag";
import { ReasoningRequest, ReasoningResponse } from "@/types/reasoning";
import { ToolDefinition, ToolExecutionRequest, ToolResult } from "@/types/tool";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN_STORAGE_KEY = "agentai_auth_token";

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setAuthToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  }
}

export function clearAuthToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  }
}

function getAuthHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...extraHeaders,
  };
  const token = getAuthToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

// --- AUTH API METHODS ---

export async function loginUser(request: LoginRequest): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || data.detail || `Login failed: ${response.status}`);
  if (data.access_token) {
    setAuthToken(data.access_token);
  }
  return data;
}

export async function registerUser(request: RegisterRequest): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || data.detail || `Registration failed: ${response.status}`);
  return data;
}

export async function fetchCurrentUser(): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
    cache: "no-store",
    headers: getAuthHeaders(),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || data.detail || `Fetch user failed: ${response.status}`);
  return data;
}

// --- AGENT STREAMING & CONTROL ENDPOINTS ---

export async function streamAgentGoal(
  request: ReasoningRequest,
  onEvent: (event: AgentEventMessage) => void,
  onError: (error: Error) => void
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/agent/reasoning/stream`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.message || errData.detail || `Streaming failed: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("ReadableStream not supported by browser.");

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const block of lines) {
        if (!block.trim()) continue;
        const dataLine = block.split("\n").find((line) => line.startsWith("data: "));
        if (dataLine) {
          const jsonStr = dataLine.replace("data: ", "").trim();
          try {
            const parsedEvent: AgentEventMessage = JSON.parse(jsonStr);
            onEvent(parsedEvent);
          } catch (e) {
            console.error("Failed to parse SSE event JSON:", e, jsonStr);
          }
        }
      }
    }
  } catch (err: unknown) {
    const error = err instanceof Error ? err : new Error("Unknown streaming error.");
    onError(error);
  }
}

export async function cancelAgentTask(taskId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/reasoning/cancel/${taskId}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error(`Cancel failed: ${response.status}`);
}

export async function approveAgentTask(taskId: string, approved: boolean = true): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/agent/reasoning/approve/${taskId}?approved=${approved}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    }
  );
  if (!response.ok) throw new Error(`Approve failed: ${response.status}`);
}

// --- EXISTING AGENT ENDPOINTS PROTECTED WITH AUTH HEADERS ---

export async function fetchHealthStatus(): Promise<HealthData> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) throw new Error(`Health check failed: ${response.status}`);
  return response.json();
}

export async function generateLLMCompletion(request: LLMRequest): Promise<LLMResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/llm/generate`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || data.detail || `LLM generation failed: ${response.status}`);
  return data;
}

export async function fetchAvailableTools(): Promise<ToolDefinition[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/tools/`, {
    cache: "no-store",
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error(`Fetch tools failed: ${response.status}`);
  return response.json();
}

export async function executeTool(request: ToolExecutionRequest): Promise<ToolResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/tools/execute`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || data.detail || `Tool execution failed: ${response.status}`);
  return data;
}

export async function solveAgentGoal(request: ReasoningRequest): Promise<ReasoningResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/reasoning/solve`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || data.detail || `Solver failed: ${response.status}`);
  return data;
}

export async function fetchSessions(): Promise<SessionMemory[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/memory/sessions`, {
    cache: "no-store",
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error(`Fetch sessions failed: ${response.status}`);
  return response.json();
}

export async function createSession(request: CreateSessionRequest): Promise<SessionMemory> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/memory/sessions`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || data.detail || `Create session failed: ${response.status}`);
  return data;
}

export async function fetchSessionById(sessionId: string): Promise<SessionMemory> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/memory/sessions/${sessionId}`, {
    cache: "no-store",
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error(`Get session failed: ${response.status}`);
  return response.json();
}

export async function addSessionMessage(
  sessionId: string,
  request: AddMessageRequest
): Promise<SessionMemory> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/memory/sessions/${sessionId}/messages`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || data.detail || `Add message failed: ${response.status}`);
  return data;
}

export async function fetchProjectContext(): Promise<ProjectContext> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/memory/context`, {
    cache: "no-store",
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error(`Fetch context failed: ${response.status}`);
  return response.json();
}

export async function indexWorkspaceCodebase(): Promise<IndexWorkspaceResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/rag/index`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || data.detail || `Indexing failed: ${response.status}`);
  return data;
}

export async function searchCodebaseRAG(request: RAGQueryRequest): Promise<RAGQueryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/rag/search`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || data.detail || `Vector search failed: ${response.status}`);
  return data;
}
