"""Agent package — lazy exports to avoid heavy import chains."""

__all__ = [
    "customer_agent",
    "generator_agent",
    "intent_agent",
    "judge_agent",
    "knowledge_agent",
    "priority_agent",
    "prompt_builder",
    "sentiment_agent",
    "validator_agent",
]


def __getattr__(name: str):
    if name == "customer_agent":
        from app.agents.customer_agent import customer_agent
        return customer_agent
    if name == "generator_agent":
        from app.agents.generator_agent import generator_agent
        return generator_agent
    if name == "prompt_builder":
        from app.agents.generator_agent import prompt_builder
        return prompt_builder
    if name == "intent_agent":
        from app.agents.intent_agent import intent_agent
        return intent_agent
    if name == "judge_agent":
        from app.agents.judge_agent import judge_agent
        return judge_agent
    if name == "knowledge_agent":
        from app.agents.knowledge_agent import knowledge_agent
        return knowledge_agent
    if name == "priority_agent":
        from app.agents.priority_agent import priority_agent
        return priority_agent
    if name == "sentiment_agent":
        from app.agents.sentiment_agent import sentiment_agent
        return sentiment_agent
    if name == "validator_agent":
        from app.agents.validator_agent import validator_agent
        return validator_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
