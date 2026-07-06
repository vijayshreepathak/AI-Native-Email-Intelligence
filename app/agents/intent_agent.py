"""Intent classification agent."""

from app.agents.base import get_llm_client
from app.constants import INTENTS
from app.prompts import INTENT_CLASSIFICATION_PROMPT
from app.state import EmailState
from app.utils.helpers import merge_node_metrics
from app.utils.logger import get_logger, log_node_execution

logger = get_logger(__name__)


async def intent_agent(state: EmailState) -> dict:
    """Classify email intent using Claude."""
    with log_node_execution(logger, "intent_agent", state.get("subject", "")) as metrics:
        client = get_llm_client()
        prompt = INTENT_CLASSIFICATION_PROMPT.format(
            subject=state.get("subject", ""),
            email=state.get("email", ""),
            intents="\n".join(f"- {i}" for i in INTENTS),
        )
        result, llm_metrics = await client.invoke(prompt, parse_json=True)
        metrics["tokens"] = llm_metrics["tokens"]
        metrics["output_summary"] = result.get("intent", "")

        return {
            "intent": result.get("intent", "bug_report"),
            **merge_node_metrics(state, "intent_agent", {**metrics, **llm_metrics}),
        }
