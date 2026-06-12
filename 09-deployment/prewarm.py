"""Prewarm pattern: load slow, immutable model weights once per worker process.

The book's claim: cold start on a fresh worker is dominated by model loading
(silero VAD, the multilingual turn detector). A `setup_fnc` runs once per
worker process before any job is accepted. Loading immutable model weights
there cuts the first session's "time to first audio" from two-plus seconds
to a couple hundred milliseconds.

What to put in setup_fnc:
- VAD model weights
- Turn detector weights
- Any other immutable, network-free, thread-safe artifact

What NOT to put in setup_fnc:
- Per-session state (user IDs, dynamic prompts)
- Live network connections to provider APIs
- Anything that mutates during a session

Run locally with:
    uv run python prewarm.py dev
"""

from __future__ import annotations

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
)
from livekit.plugins import cartesia, deepgram, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()


def my_prewarm(proc: JobProcess) -> None:
    """Runs once per worker process before any job is accepted.

    Anything stored on `proc.userdata` becomes available on every subsequent
    `ctx.proc.userdata` lookup in the entrypoint.
    """
    proc.userdata["vad"] = silero.VAD.load()
    proc.userdata["turn_detection"] = MultilingualModel()


server = AgentServer()
server.setup_fnc = my_prewarm


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=("You are a friendly voice assistant. Speak in short sentences.")
        )


@server.rtc_session(agent_name="voiceagents-handbook-ch09")
async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()
    session = AgentSession(
        # Reuse the pre-loaded model weights from setup_fnc.
        vad=ctx.proc.userdata["vad"],
        turn_detection=ctx.proc.userdata["turn_detection"],
        stt=deepgram.STT(model="nova-3"),
        llm=openai.LLM(model="gpt-4.1-mini"),
        tts=cartesia.TTS(
            model="sonic-3",
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        ),
    )
    await session.start(agent=Assistant(), room=ctx.room)
    await session.generate_reply(instructions="Greet the user warmly.")


if __name__ == "__main__":
    agents.cli.run_app(server)
