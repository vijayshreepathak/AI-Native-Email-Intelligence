"use client";

import { Modal } from "@/components/Modal";

interface HowToUsePanelProps {
  open: boolean;
  onClose: () => void;
}

const STEPS = [
  {
    step: 1,
    title: "Start the backend",
    body: "Open a terminal in the project folder and run:",
    code: "python cli.py serve",
    note: "API runs at http://127.0.0.1:8000. Green “healthy” badge in the header confirms it’s live.",
  },
  {
    step: 2,
    title: "Open this dashboard",
    body: "In another terminal:",
    code: "cd dashboard && npm run dev",
    note: "Visit http://localhost:3000. Click Sync if metrics show dashes.",
  },
  {
    step: 3,
    title: "Generate a reply (quick test)",
    body: "In Copilot Playground, keep “Generate” selected. Fill in customer name, subject, and email body (or use the sample). Click Generate Reply.",
    note: "Wait ~30–60s. The right panel shows intent, priority, sentiment, the AI reply, validation checks, and retrieved knowledge docs.",
  },
  {
    step: 4,
    title: "Run full evaluation",
    body: "Switch to “Evaluate”. Paste an expected reference reply in the new field (ground truth). Click Run Evaluation.",
    note: "Gets BERTScore, embedding similarity, LLM judge scores, and an overall weighted score. Metrics update in the top strip and charts.",
  },
  {
    step: 5,
    title: "Embed knowledge (first-time setup)",
    body: "If “Indexing” shows instead of “Indexed”, run once:",
    code: "python scripts/embed_knowledge.py",
    note: "Loads policies and FAQs into ChromaDB for RAG retrieval.",
  },
  {
    step: 6,
    title: "Generate the dataset",
    body: "Requires ANTHROPIC_API_KEY in .env:",
    code: "python scripts/generate_dataset.py generate",
    note: "Creates 300 emails → train.json (220), validation.json (40), test.json (40). Resumes from checkpoint if interrupted.",
  },
  {
    step: 7,
    title: "Batch evaluate via CLI",
    body: "Run evaluation on test split:",
    code: "python cli.py evaluate-dataset --split test --limit 5",
    note: "Processes emails through the full pipeline and saves results to results/evaluation.json.",
  },
  {
    step: 8,
    title: "Read the metrics",
    body: "Top strip: Avg Score, Latency, Tokens, Hallucination rate. Bottom charts: best intents and LLM judge radar. Lower hallucination % is better.",
    note: "Use API directly: POST /generate, /evaluate, /predict · GET /dashboard, /health",
  },
];

export function HowToUsePanel({ open, onClose }: HowToUsePanelProps) {
  return (
    <Modal open={open} onClose={onClose} title="How to Use" subtitle="End-to-end guide in 8 simple steps" wide>
      <ol className="space-y-4">
        {STEPS.map((s) => (
          <li key={s.step} className="flex gap-3">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--accent)] text-xs font-bold text-black">
              {s.step}
            </span>
            <div className="min-w-0 flex-1">
              <h3 className="text-sm font-semibold text-[var(--text)]">{s.title}</h3>
              <p className="mt-1 text-[11px] leading-relaxed text-[var(--text-muted)]">{s.body}</p>
              {s.code && (
                <code className="mt-2 block rounded-lg border border-[var(--border)] bg-black px-3 py-2 text-[11px] text-[var(--accent)]">
                  {s.code}
                </code>
              )}
              {s.note && (
                <p className="mt-2 flex items-start gap-1.5 text-[10px] text-[var(--success)]">
                  <span className="mt-0.5 shrink-0">→</span>
                  {s.note}
                </p>
              )}
            </div>
          </li>
        ))}
      </ol>
    </Modal>
  );
}
