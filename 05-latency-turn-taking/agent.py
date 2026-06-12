"""Chapter 5 baseline: explicit defaults for turn handling.

Adaptive interruption is on. Endpointing is the conservative 0.5 / 3.0 window.
Preemptive generation is on (default) but preemptive TTS is off. This is the
"recommended starting point" from section 6 of the chapter, written out
explicitly so the next engineer can see the timing posture at a glance.

Run on a real phone if you can. The terminal will lie to you about cadence.
"""

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    TurnHandlingOptions,
)
from livekit.plugins import cartesia, deepgram, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a helpful voice assistant. "
                "Keep responses short and conversational. "
                "Do not use markdown, lists, or headings. "
                "The user will hear this, not read it."
            )
        )


server = AgentServer()


@server.rtc_session(agent_name="voiceagents-handbook-ch05")
async def my_agent(ctx: JobContext):
    await ctx.connect()
    session = AgentSession(
        turn_handling=TurnHandlingOptions(
            turn_detection=MultilingualModel(),
            endpointing={
                "mode": "fixed",
                "min_delay": 0.5,
                "max_delay": 3.0,
            },
            interruption={
                "mode": "adaptive",
                "min_duration": 0.5,
                "min_words": 0,
            },
            preemptive_generation={
                "preemptive_tts": False,
            },
        ),
        # min_consecutive_speech_delay smooths the seam between a say()
        # and a generate_reply() that lands right after a tool call.
        min_consecutive_speech_delay=0.2,
        vad=silero.VAD.load(),
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
