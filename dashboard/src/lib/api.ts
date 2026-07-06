const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

import { parseApiError } from "./errors";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(parseApiError(text || `Request failed (${res.status})`));
  }
  return res.json();
}

export const api = {
  health: () => request<{ status: string; version: string; model: string; chroma_available: boolean }>("/health"),
  dashboard: () => request<{ metrics: import("./types").DashboardMetrics }>("/dashboard"),
  generate: (body: { subject: string; email: string; customer_name?: string; company?: string }) =>
    request<import("./types").GenerateResult>("/generate", { method: "POST", body: JSON.stringify(body) }),
  evaluate: (body: { subject: string; email: string; expected_response: string; customer_name?: string }) =>
    request<import("./types").EvaluateResult>("/evaluate", { method: "POST", body: JSON.stringify(body) }),
  predict: (body: { subject: string; email: string }) =>
    request<{ intent: string; priority: string; sentiment: string; customer_type: string; latency_ms: number }>(
      "/predict",
      { method: "POST", body: JSON.stringify(body) }
    ),
};
