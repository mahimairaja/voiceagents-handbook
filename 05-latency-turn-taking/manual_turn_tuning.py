"""Chapter 5 variant: VAD-only turn handling with explicit endpointing.

This is the "if you can't run adaptive" baseline. No turn-detector model.
No adaptive interruption. Pure VAD plus an endpointing window you set
yourself. Useful when you are running outside LiveKit Cloud and want
predictable, deterministic timing behavior.

The two failure modes you are now fully responsible for:

  - Push min_delay too low (below ~0.2) and you clip users mid-thought.
    The hesitation gap becomes constant.
  - Push min_delay too high (above ~0.8) and the agent feels slow on
    short, predictable turns.

The right setting depends on the user population. A drive-thru menu can
get away with 0.3. A medical intake line probably wants 0.7. Pick by
listening, not by reading the terminal.
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

load_dotenv()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a helpful voice assistant. "
                "Keep responses very short, one sentence when possible. "
                "Do not use markdown, lists, or headings."
            )
        )


server = AgentServer()


@server.rtc_session(agent_name="voiceagents-handbook-ch05")
async def my_agent(ctx: JobContext):
    await ctx.connect()
    session = AgentSession(
        turn_handling=TurnHandlingOptions(
            # No turn_detection model. VAD silence plus the endpointing
            # window decides when a turn ends.
            turn_detection=None,
            endpointing={
                "mode": "fixed",
                # 0.3 is tight. Try 0.5 for a more forgiving baseline,
                # 0.7 for users who pause mid-sentence often.
                "min_delay": 0.3,
                "max_delay": 3.0,
            },
            # VAD-only interruption. No backchannel detection. Acknowledgments
            # will sometimes cut the agent off. Raise min_duration to 0.7 or
            # min_words to 2 to compensate.
            interruption={
                "mode": "vad",
                "min_duration": 0.5,
                "min_words": 0,
            },
        ),
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-3"),
        llm=openai.LLM(model="gpt-4.1-mini"),
        tts=cartesia.TTS(
            model="sonic-3",
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        ),
    )
    await session.start(agent=Assistant(), room=ctx.room)
    await session.generate_reply(instructions="Greet the user in one short sentence.")


if __name__ == "__main__":
    agents.cli.run_app(server)
