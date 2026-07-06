"""Dashboard metrics aggregation service."""

from collections import defaultdict
from datetime import datetime
from typing import Any

from app.config import get_settings
from app.models import DashboardMetrics
from app.utils.helpers import load_json, save_json
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DashboardService:
    """Aggregates evaluation results into dashboard metrics."""

    def __init__(self) -> None:
        settings = get_settings()
        self._evaluation_path = settings.evaluation_results_path
        self._dashboard_path = settings.dashboard_path
        self._generated_path = settings.generated_results_path

    def _load_evaluations(self) -> list[dict[str, Any]]:
        if not self._evaluation_path.exists():
            return []
        data = load_json(self._evaluation_path)
        return data if isinstance(data, list) else []

    def compute_metrics(self) -> DashboardMetrics:
        """Compute aggregated dashboard metrics from evaluation results."""
        evaluations = self._load_evaluations()
        if not evaluations:
            return DashboardMetrics()

        scores: list[float] = []
        latencies: list[float] = []
        tokens: list[int] = []
        intent_scores: dict[str, list[float]] = defaultdict(list)
        hallucination_flags: list[bool] = []
        judge_scores: dict[str, list[float]] = defaultdict(list)

        for eval_item in evaluations:
            overall = eval_item.get("overall_score", 0.0)
            scores.append(overall)

            intent = eval_item.get("intent", "unknown")
            intent_scores[intent].append(overall)

            node_metrics = eval_item.get("node_metrics", {})
            total_latency = sum(
                m.get("latency_ms", 0) for m in node_metrics.values()
            )
            latencies.append(total_latency)

            gen_reply = eval_item.get("generated_reply", {})
            tokens.append(gen_reply.get("tokens", 0))

            judge = eval_item.get("judge_score", {})
            hallucination_score = judge.get("hallucination", 1.0)
            hallucination_flags.append(hallucination_score < 0.7)

            for criterion in [
                "correctness",
                "completeness",
                "empathy",
                "professionalism",
                "actionability",
                "safety",
                "hallucination",
                "policy_adherence",
            ]:
                if criterion in judge:
                    judge_scores[criterion].append(judge[criterion])

        intent_averages = {
            intent: sum(vals) / len(vals)
            for intent, vals in intent_scores.items()
        }
        sorted_intents = sorted(intent_averages.items(), key=lambda x: x[1], reverse=True)

        judge_distribution = {
            k: round(sum(v) / len(v), 4) for k, v in judge_scores.items()
        }

        return DashboardMetrics(
            average_score=round(sum(scores) / len(scores), 4) if scores else 0.0,
            average_latency_ms=round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
            average_tokens=round(sum(tokens) / len(tokens), 1) if tokens else 0.0,
            total_processed=len(evaluations),
            top_intents=[
                {"intent": k, "avg_score": round(v, 4)} for k, v in sorted_intents[:5]
            ],
            worst_intents=[
                {"intent": k, "avg_score": round(v, 4)} for k, v in sorted_intents[-5:]
            ],
            hallucination_rate=round(
                sum(hallucination_flags) / len(hallucination_flags), 4
            )
            if hallucination_flags
            else 0.0,
            judge_distribution=judge_distribution,
            last_updated=datetime.utcnow(),
        )

    def save_dashboard(self) -> DashboardMetrics:
        """Compute and persist dashboard metrics."""
        metrics = self.compute_metrics()
        save_json(self._dashboard_path, metrics.model_dump(mode="json"))
        logger.info("Dashboard saved with %d evaluations", metrics.total_processed)
        return metrics

    def append_evaluation(self, result: dict[str, Any]) -> None:
        """Append evaluation result and update dashboard."""
        evaluations = self._load_evaluations()
        evaluations.append(result)
        save_json(self._evaluation_path, evaluations)
        self.save_dashboard()

    def append_generation(self, result: dict[str, Any]) -> None:
        """Append generation result."""
        if self._generated_path.exists():
            data = load_json(self._generated_path)
            if not isinstance(data, list):
                data = []
        else:
            data = []
        data.append(result)
        save_json(self._generated_path, data)


_dashboard_service: DashboardService | None = None


def get_dashboard_service() -> DashboardService:
    """Singleton dashboard service."""
    global _dashboard_service
    if _dashboard_service is None:
        _dashboard_service = DashboardService()
    return _dashboard_service
