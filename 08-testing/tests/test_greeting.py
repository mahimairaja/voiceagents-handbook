"""Single-turn test: when a caller says hello, the agent greets them back."""

from __future__ import annotations

import pytest
from livekit.agents import AgentSession, inference


@pytest.mark.asyncio
async def test_greets_the_caller(
    agent_session: AgentSession,
    judge_llm: inference.LLM,
) -> None:
    result = await agent_session.run(user_input="Hello")

    await (
        result.expect.next_event()
        .is_message(role="assistant")
        .judge(
            judge_llm,
            intent="Greets the caller warmly and offers to help.",
        )
    )
    result.expect.no_more_events()


@pytest.mark.asyncio
async def test_does_not_read_out_urls(
    agent_session: AgentSession,
    judge_llm: inference.LLM,
) -> None:
    result = await agent_session.run(user_input="Where can I find more info online?")

    await (
        result.expect.next_event()
        .is_message(role="assistant")
        .judge(
            judge_llm,
            intent=(
                "Acknowledges the caller's question without reading out a "
                "URL or website address letter by letter."
            ),
        )
    )
