"""Chapter 1: The baseline voice agent.

The smallest LiveKit agent that does something useful. Five components
(VAD, STT, LLM, TTS, plus turn detection) wired into an AgentSession.
Uses LiveKit Inference for STT, LLM, and TTS routing. Subsequent
chapters extend this baseline.
"""

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    inference,
)
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a helpful voice assistant. "
                "Keep responses short, conversational, and without markdown."
            )
        )


server = AgentServer()


@server.rtc_session(agent_name="voiceagents-handbook-ch01")
async def my_agent(ctx: JobContext):
    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="en"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(
            model="cartesia/sonic-3",
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        ),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(agent=Assistant(), room=ctx.room)
    await session.generate_reply(instructions="Greet the user warmly.")


if __name__ == "__main__":
    agents.cli.run_app(server)
