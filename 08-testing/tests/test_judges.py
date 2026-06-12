"""Conversation-level test using `JudgeGroup`.

`JudgeGroup` runs several built-in judges across a full session history
and aggregates their verdicts. This is the test you keep running on
every deploy: it does not assert on specific phrasings or tool argument
shapes; it asserts that the agent, across a multi-turn intake, completed
the task, grounded its responses, used tools correctly, stayed on topic,
and did not say anything unsafe.
"""

from __future__ import annotations

import pytest
from livekit.agents import AgentSession, inference
from livekit.agents.evals import (
    JudgeGroup,
    accuracy_judge,
    relevancy_judge,
    safety_judge,
    task_completion_judge,
    tool_use_judge,
)


@pytest.mark.asyncio
async def test_full_intake_conversation(
    agent_session: AgentSession,
) -> None:
    await agent_session.run(user_input="Hi, I have a leak in my bathroom.")
    await agent_session.run(user_input="I'm at 123 Maple Street.")
    await agent_session.run(user_input="Can you send someone Thursday at 3 PM?")

    judges = JudgeGroup(
        llm="openai/gpt-4o-mini",
        judges=[
            task_completion_judge(),
            accuracy_judge(),
            tool_use_judge(),
            relevancy_judge(),
            safety_judge(),
        ],
    )

    result = await judges.evaluate(agent_session.history)
    assert result.all_passed, f"Failures: {result.judgments}"


@pytest.mark.asyncio
async def test_pricing_conversation_passes_judges() -> None:
    """A pricing-only conversation evaluated by a smaller judge set."""

    async with (
        inference.LLM(model="openai/gpt-4.1-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        from agent import Assistant

        await session.start(Assistant())

        await session.run(user_input="What do you charge for a leak repair?")
        await session.run(user_input="And a water heater install?")

        judges = JudgeGroup(
            llm="openai/gpt-4o-mini",
            judges=[
                accuracy_judge(),
                tool_use_judge(),
                relevancy_judge(),
            ],
        )

        result = await judges.evaluate(session.history)
        assert result.all_passed, f"Failures: {result.judgments}"
