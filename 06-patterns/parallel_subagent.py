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
                "You are answering the phone for ACME Plumbing. Be helpful, friendly, and direct."
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


def run_observer(session: AgentSession) -> None:
    """Attach a side-channel observer to the session.

    Watches user transcripts and scores them against a rubric. Persists the
    cumulative score on the session so anything else in the call can read it
    via ``session.rubric_score``. The observer never publishes audio back to
    the room; outputs go to log handlers and ``alert_supervisor``.

    This function is synchronous and returns immediately. Do not ``await`` or
    ``asyncio.create_task`` it.
    """

    # Stash cumulative state on the session itself so other call-scoped code
    # (or a shutdown hook) can read the final score without holding a closure.
    session.rubric_score = 0.0

    @session.on("conversation_item_added")
    def _on_conversation_item(event):
        item = getattr(event, "item", None)
        if item is None:
            return
        if getattr(item, "role", None) != "user":
            return
        transcript = getattr(item, "text_content", "") or ""
        if not transcript:
            return
        asyncio.create_task(_score_and_alert(session, transcript))


async def _score_and_alert(session: AgentSession, transcript: str) -> None:
    """Run the (potentially slow) scoring outside the event handler."""

    score = await score_against_rubric(transcript)
    session.rubric_score = getattr(session, "rubric_score", 0.0) + score
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

    # Attach the observer. In production the observer runs as its own
    # participant in the same room with a subscribe-only token. This
    # in-process variant shows the analysis shape; deploy it as a separate
    # participant when you ship.
    run_observer(session)

    await session.start(
        agent=PrimaryAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(),
        room_output_options=RoomOutputOptions(),
    )
    await session.generate_reply(instructions="Greet the caller warmly.")


if __name__ == "__main__":
    agents.cli.run_app(server)
