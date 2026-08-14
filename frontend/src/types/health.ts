export interface HealthData {
  status: "healthy" | "degraded" | "unhealthy";
  service: string;
  environment: string;
  timestamp: string;
  database: "connected" | "disconnected";
  modules: Record<string, string>;
}
