"""Chapter 5 variant: preemptive generation, including preemptive TTS.

Preemptive generation starts the LLM as soon as STT emits a final transcript,
before the turn detector has confirmed the turn is closed. Preemptive TTS goes
one step further and starts synthesizing audio against that preemptive LLM
response. Both trade wasted compute for lower perceived latency.

The footgun (section 4 of the chapter): preemptive generation only helps if
the LLM has a fast time to first token. gpt-4.1-mini is a good fit. A full
frontier reasoning model with hidden thinking tokens will not have produced a
token by the time the turn detector fires, and preemptive generation buys you
nothing. If you flip these flags on and hear no improvement, the LLM choice
is usually the answer, not the configuration.

max_speech_duration caps preemption for unusually long utterances (default
10s). max_retries caps the number of preemptive attempts per turn (default 3).
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
                "Do not use markdown, lists, or headings."
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
            preemptive_generation={
                # Flip preemptive TTS on. Costs you wasted synthesis when the
                # preemptive response gets canceled. Shaves about 150 ms off
                # perceived latency when it lands.
                "preemptive_tts": True,
                "max_speech_duration": 10.0,
                "max_retries": 3,
            },
        ),
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-3"),
        # gpt-4.1-mini has a fast time to first token. Preemptive generation
        # is meaningful here. With a slow model, it would be a no-op.
        llm=openai.LLM(model="gpt-4.1-mini"),
        tts=cartesia.TTS(
            model="sonic-3",
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        ),
    )
    await session.start(agent=Assistant(), room=ctx.room)
    await session.generate_reply(instructions="Greet the user briefly and ask what they need.")


if __name__ == "__main__":
    agents.cli.run_app(server)
