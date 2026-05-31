"""Pattern 4: the observer agent (parallel subagent).

An observer agent listens to a conversation but does not participate in it. It
joins the same LiveKit room as the primary agent and the user, subscribes to
their audio tracks, and emits its outputs sideways (to a dashboard, a database,
a Slack channel, an escalation queue) rather than back into the room as speech.

This file shows the shape of both sides: a primary conversational agent for
the user to talk to, and an observer that scores the conversation against a
rubric on a side channel.

In production, the observer is a separate participant joined with a
subscribe-only access token (canPublish=False, canSubscribe=True), enforced at
the LiveKit server level. The book section: Chapter 6, Section 4.

A useful rule: an observer that can publish audio is not an observer. It is a
misconfigured second agent waiting to surprise you in production.
"""

import asyncio
import logging

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    RoomInputOptions,
    RoomOutputOptions,
)
from livekit.plugins import cartesia, deepgram, openai, silero

load_dotenv()

logger = logging.getLogger("parallel_subagent")
logger.setLevel(logging.INFO)

server = AgentServer()

RUBRIC_THRESHOLD = 0.4


class PrimaryAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are answering the phone for ACME Plumbing. "
                "Be helpful, friendly, and direct."
            )
        )


async def score_against_rubric(transcript: str) -> float:
    """Score a transcript fragment against a quality rubric.

    Production observers swap this for an LLM call against a defined rubric or
    a small classifier model. This stub returns a low score for transcripts
    that contain common frustration signals so the alert path is exercised.
    """

    frustration_signals = ("manager", "frustrated", "cancel", "lawsuit")
    if any(signal in transcript.lower() for signal in frustration_signals):
        return 0.1
    return 0.9


async def alert_supervisor(transcript: str) -> None:
    """Side-channel output. Send to Slack, PagerDuty, a webhook, a dashboard."""

    logger.warning("supervisor alert: %s", transcript)


async def run_observer(session: AgentSession) -> None:
    """Watch the user's transcripts and score them against a rubric.

    The observer never publishes audio back to the room. It only reads the
    conversation and emits side-channel outputs.
    """

    rubric_score = 0.0
    async for event in session.events("conversation_item_added"):
        item = getattr(event, "item", None)
        if item is None:
            continue
        if getattr(item, "role", None) != "user":
            continue
        transcript = getattr(item, "text_content", "") or ""
        if not transcript:
            continue
        score = await score_against_rubric(transcript)
        rubric_score += score
        if score < RUBRIC_THRESHOLD:
            await alert_supervisor(transcript)


@server.rtc_session(agent_name="voiceagents-handbook-ch06")
async def my_agent(ctx: JobContext):
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

    # Start the observer in the background. In production the observer runs as
    # its own participant in the same room with a subscribe-only token. This
    # in-process variant shows the analysis shape; deploy it as a separate
    # participant when you ship.
    observer_task = asyncio.create_task(run_observer(session))

    await session.start(
        agent=PrimaryAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(),
        room_output_options=RoomOutputOptions(),
    )
    await session.generate_reply(instructions="Greet the caller warmly.")

    async def cancel_observer():
        observer_task.cancel()

    ctx.add_shutdown_callback(cancel_observer)


if __name__ == "__main__":
    agents.cli.run_app(server)
