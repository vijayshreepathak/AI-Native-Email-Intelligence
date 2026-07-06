const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

import { parseApiError } from "./errors";

let tokenGetter: (() => Promise<string | null>) | null = null;

export function configureApiAuth(fn: () => Promise<string | null>) {
  tokenGetter = fn;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };

  if (tokenGetter) {
    const token = await tokenGetter();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(parseApiError(text || `Request failed (${res.status})`));
  }
  return res.json();
}

export const api = {
  health: () =>
    request<{
      status: string;
      version: string;
      model: string;
      chroma_available: boolean;
      llm_provider?: string;
      fallback_available?: boolean;
      fallback_provider?: string;
      fallback_used?: boolean;
      retries?: number;
      provider_latency_ms?: number;
      providers?: Record<string, boolean>;
    }>("/health"),
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
