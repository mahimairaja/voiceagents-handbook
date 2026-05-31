"""Surface-agnostic baseline agent.

The agent makes no assumptions about whether the participant arrived
over SIP (phone), WebRTC (browser), or a native mobile SDK. Audio is
audio. The session config below works well enough across all three.

Run with:
    uv run python agent.py dev
"""

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, JobContext
from livekit.plugins import cartesia, deepgram, openai, silero

load_dotenv()

server = AgentServer()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a friendly receptionist for ACME Plumbing. "
                "Keep responses short. Confirm important details out loud. "
                "Do not read URLs or email addresses character by character."
            )
        )


@server.rtc_session(agent_name="voiceagents-handbook-ch07")
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
    await session.start(agent=Assistant(), room=ctx.room)
    await session.generate_reply(instructions="Greet the user warmly.")


if __name__ == "__main__":
    agents.cli.run_app(server)
