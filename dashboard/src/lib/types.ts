export interface DashboardMetrics {
  average_score: number;
  average_latency_ms: number;
  average_tokens: number;
  total_processed: number;
  top_intents: { intent: string; avg_score: number }[];
  worst_intents: { intent: string; avg_score: number }[];
  hallucination_rate: number;
  judge_distribution: Record<string, number>;
  last_updated?: string;
}

export interface EvaluateResult {
  subject: string;
  email: string;
  generated_reply: {
    reply: string;
    confidence: number;
    reasoning: string;
    citations: string[];
    tokens: number;
    latency_ms: number;
  };
  validated_reply: {
    final_reply: string;
    validation: {
      passed: boolean;
      overall_score: number;
      checks: { check: string; passed: boolean; score: number; details: string }[];
      issues: string[];
    };
  };
  bertscore: { precision: number; recall: number; f1: number };
  embedding_score: { cosine_similarity: number };
  judge_score: Record<string, number | string>;
  overall_score: number;
  feedback: string;
  node_metrics: Record<string, { latency_ms: number; tokens: number }>;
}

export interface GenerateResult {
  subject: string;
  intent: string;
  priority: string;
  sentiment: string;
  customer_type: string;
  retrieved_documents: { id: string; title: string; score: number; node: string }[];
  generated_reply: EvaluateResult["generated_reply"];
  validated_reply: EvaluateResult["validated_reply"];
  overall_latency_ms: number;
}

export interface HealthStatus {
  status: string;
  version: string;
  model: string;
  chroma_available: boolean;
  llm_provider?: string;
  fallback_available?: boolean;
}
