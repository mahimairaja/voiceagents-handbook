"""Multi-turn test exercising a price-quote and booking conversation.

This is the canonical shape of a voice agent test the chapter teaches:
three assertions across one conversation turn. The tool call, the tool
output, and the spoken response are each checked independently.
"""

from __future__ import annotations

import pytest
from livekit.agents import AgentSession, inference, mock_tools

from agent import Assistant


@pytest.mark.asyncio
async def test_quotes_a_drain_cleaning(
    agent_session: AgentSession,
    judge_llm: inference.LLM,
) -> None:
    result = await agent_session.run(user_input="How much would it cost to get a drain cleaned?")

    # Agent should call the pricing tool with the right service name.
    result.expect.next_event().is_function_call(
        name="get_service_price",
        arguments={"service": "drain cleaning"},
    )

    # Tool returns the expected output.
    result.expect.next_event().is_function_call_output()

    # Agent's spoken response should quote the price in words.
    await (
        result.expect.next_event()
        .is_message(role="assistant")
        .judge(
            judge_llm,
            intent=(
                "Quotes the price of a drain cleaning as one forty-nine, "
                "spoken in words rather than digits, and does not read out "
                "any URL or website."
            ),
        )
    )

    result.expect.no_more_events()


@pytest.mark.asyncio
async def test_books_a_visit(
    agent_session: AgentSession,
    judge_llm: inference.LLM,
    simulated_user,
) -> None:
    result = await simulated_user(
        [
            "Hi, I'd like to book a drain cleaning.",
            "Thursday at 3 PM works for me.",
        ]
    )

    # Somewhere in the final turn, the agent should call book_appointment.
    result.expect.contains_function_call(
        name="book_appointment",
        arguments={"service": "drain cleaning"},
    )

    # And it should confirm the booking out loud.
    await result.expect.contains_message(role="assistant").judge(
        judge_llm,
        intent="Confirms the booking for a drain cleaning at the requested time.",
    )


@pytest.mark.asyncio
async def test_handles_unavailable_slot_gracefully(
    judge_llm: inference.LLM,
) -> None:
    """When booking fails, the agent should recover without panicking."""

    async with AgentSession(llm=judge_llm) as session:
        await session.start(Assistant())

        def _raise_unavailable(*args, **kwargs):
            raise RuntimeError("That slot is unavailable.")

        with mock_tools(
            Assistant,
            {"book_appointment": _raise_unavailable},
        ):
            result = await session.run(
                user_input="Can you book me for Thursday at 3 PM for a drain cleaning?"
            )

            await result.expect.contains_message(role="assistant").judge(
                judge_llm,
                intent=(
                    "Tells the caller the slot isn't available and offers "
                    "to find an alternative time."
                ),
            )
