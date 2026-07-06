"""Priority/urgency classification agent."""

from app.agents.base import get_llm_client
from app.prompts import PRIORITY_CLASSIFICATION_PROMPT
from app.state import EmailState
from app.utils.helpers import merge_node_metrics
from app.utils.logger import get_logger, log_node_execution

logger = get_logger(__name__)


async def priority_agent(state: EmailState) -> dict:
    """Detect email urgency priority."""
    with log_node_execution(logger, "priority_agent", state.get("intent", "")) as metrics:
        client = get_llm_client()
        prompt = PRIORITY_CLASSIFICATION_PROMPT.format(
            subject=state.get("subject", ""),
            email=state.get("email", ""),
            intent=state.get("intent", ""),
        )
        result, llm_metrics = await client.invoke(prompt, parse_json=True)
        metrics["tokens"] = llm_metrics["tokens"]
        metrics["output_summary"] = result.get("priority", "")

        return {
            "priority": result.get("priority", "medium"),
            **merge_node_metrics(state, "priority_agent", {**metrics, **llm_metrics}),
        }
