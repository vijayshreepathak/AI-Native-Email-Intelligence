"""Quick smoke test for Claude + Gemini fallback."""
import asyncio

from app.config import get_settings
from app.agents import base as llm_base


async def main() -> None:
    get_settings.cache_clear()
    llm_base._llm_client = None
    client = llm_base.get_llm_client()
    result, metrics = await client.invoke(
        'Return JSON only: {"status": "ok"}',
        parse_json=True,
    )
    print("provider:", metrics.get("provider"))
    print("model:", metrics.get("model"))
    print("result:", result)


if __name__ == "__main__":
    asyncio.run(main())
