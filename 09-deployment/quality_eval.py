"""Quality evaluation in production: run `JudgeGroup` on a shutdown callback.

A web service can be healthy (all 200s, low latency, no errors) and still serve
users badly: wrong answers, broken flows, things it should never say. Health
checks do not catch that. The discipline that does is running the same judges
you use in your test suite against the *live* transcript, on every session, as
it closes.

This file is the production half of the Chapter 8 test loop. `JudgeGroup` runs
on the session-end shutdown callback against `session.history`. On LiveKit Cloud
the verdicts surface as session tags in the dashboard (auto-tagged as
`lk.judge.<name>:<verdict>`), so you can filter for `safety:fail` and pull the
exact conversations that need a human. The failures you find here become the
test cases that go back into your pytest suite.

Run locally with:
    uv run python quality_eval.py dev
"""

from __future__ import annotations

import logging

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    RunContext,
    function_tool,
)
from livekit.agents.evals import (
    JudgeGroup,
    accuracy_judge,
    relevancy_judge,
    safety_judge,
    task_completion_judge,
)
from livekit.plugins import cartesia, deepgram, openai, silero

load_dotenv()

logger = logging.getLogger("quality-eval")

server = AgentServer()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a friendly voice assistant for ACME Plumbing. "
                "Greet callers warmly, ask how you can help, and offer to look up "
                "appointment availability when callers want to book service. "
                "Speak in short sentences. Never read URLs or markdown out loud."
            )
        )

    @function_tool
    async def get_next_available_slot(self, context: RunContext) -> dict:
        """Return the next available service appointment slot.

        Use this when the caller asks about scheduling, availability, or when
        they want to book a plumber visit.
        """
        return {
            "slot_id": "slot-001",
            "starts_at": "2026-06-02T09:00:00-04:00",
            "duration_minutes": 60,
            "technician": "Jordan",
        }


@server.rtc_session(agent_name="voiceagents-handbook-ch09")
async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-3"),
        llm=openai.LLM(model="gpt-4.1-mini"),
        tts=cartesia.TTS(
            model="sonic-3",
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        ),
    )

    async def evaluate_on_close() -> None:
        """Judge the finished conversation as the session shuts down.

        A cheaper model than the agent's own LLM is the right call here: the
        judge reads the transcript once, it does not need to be conversational.
        """
        judges = JudgeGroup(
            llm="openai/gpt-4o-mini",
            judges=[
                accuracy_judge(),
                relevancy_judge(),
                safety_judge(),
                task_completion_judge(),
            ],
        )
        result = await judges.evaluate(session.history)
        if result.all_passed:
            logger.info("session passed all judges")
        else:
            logger.warning("session failed judges: %s", result.judgments)

    ctx.add_shutdown_callback(evaluate_on_close)

    await session.start(agent=Assistant(), room=ctx.room)
    await session.generate_reply(
        instructions="Greet the caller warmly and ask how you can help today."
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
