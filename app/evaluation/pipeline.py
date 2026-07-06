"""Evaluation pipeline nodes for LangGraph."""

from app.evaluation.bertscore import compute_bertscore
from app.evaluation.embedding_similarity import compute_embedding_similarity
from app.evaluation.overall_score import aggregate_feedback, compute_overall_score
from app.state import EmailState
from app.utils.helpers import merge_node_metrics
from app.utils.logger import get_logger, log_node_execution

logger = get_logger(__name__)


async def embedding_evaluation_node(state: EmailState) -> dict:
    """Compute embedding cosine similarity."""
    generated = state.get("generated_reply", {})
    reply = generated.get("reply", "")
    expected = state.get("expected_response", "")

    with log_node_execution(logger, "embedding_evaluation", reply[:100]) as metrics:
        score = compute_embedding_similarity(reply, expected)
        metrics["output_summary"] = f"similarity={score['cosine_similarity']}"
        return {
            "embedding_score": score,
            **merge_node_metrics(state, "embedding_evaluation", metrics),
        }


async def bertscore_node(state: EmailState) -> dict:
    """Compute BERTScore metrics."""
    generated = state.get("generated_reply", {})
    reply = generated.get("reply", "")
    expected = state.get("expected_response", "")

    with log_node_execution(logger, "bertscore", reply[:100]) as metrics:
        score = compute_bertscore(reply, expected)
        metrics["output_summary"] = f"f1={score['f1']}"
        return {
            "bertscore": score,
            **merge_node_metrics(state, "bertscore", metrics),
        }


async def final_report_node(state: EmailState) -> dict:
    """Compute overall score and aggregate feedback."""
    with log_node_execution(logger, "final_report", "") as metrics:
        overall = compute_overall_score(
            state.get("bertscore", {}),
            state.get("embedding_score", {}),
            state.get("judge_score", {}),
        )
        validated = state.get("validated_reply", {})
        validation_data = validated.get("validation", {})
        feedback = aggregate_feedback(
            state.get("judge_score", {}),
            validation_data,
        )
        metrics["output_summary"] = f"overall={overall}"
        return {
            "overall_score": overall,
            "feedback": feedback,
            **merge_node_metrics(state, "final_report", metrics),
        }
