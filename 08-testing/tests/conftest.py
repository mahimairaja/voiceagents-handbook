"""Shared pytest fixtures for the Chapter 8 test suite.

These fixtures match the pattern the chapter teaches:

- `judge_llm` builds an `inference.LLM` once per test and tears it down cleanly.
- `agent_session` yields a started `AgentSession` wired to the same LLM,
  with the `Assistant` from `agent.py` already running.
- `simulated_user` is a small helper that drives one or more turns through
  the session and returns the `RunResult` of the final turn.

The fixtures are async because `AgentSession` and `inference.LLM` are async
context managers. `pytest-asyncio` is configured in `asyncio_mode = "auto"`
in `pyproject.toml`, so any `async def` test or fixture is picked up.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

import pytest_asyncio
from livekit.agents import AgentSession, inference

from agent import Assistant


@pytest_asyncio.fixture
async def judge_llm() -> AsyncIterator[inference.LLM]:
    """A cheap LLM used both to drive the agent and to judge its responses."""
    async with inference.LLM(model="openai/gpt-4.1-mini") as llm:
        yield llm


@pytest_asyncio.fixture
async def agent_session(
    judge_llm: inference.LLM,
) -> AsyncIterator[AgentSession]:
    """A started `AgentSession` running the `Assistant` from agent.py."""
    async with AgentSession(llm=judge_llm) as session:
        await session.start(Assistant())
        yield session


@pytest_asyncio.fixture
def simulated_user(agent_session: AgentSession):
    """A helper that feeds a sequence of user turns into the session.

    Returns the `RunResult` of the last turn so the caller can assert on it.
    """

    async def _drive(turns: str | Sequence[str]):
        if isinstance(turns, str):
            turns = [turns]
        result = None
        for turn in turns:
            result = await agent_session.run(user_input=turn)
        return result

    return _drive
