"""Chat-shaped prompt: loads prompts/chat.txt so you can hear the failure modes.

Run this side by side with agent.py. The pipeline, models, and voice are identical.
Only the instructions differ. Listen for: asterisks read out loud, URLs spelled
letter by letter, long paragraphs, and lawyer-style hedge stuffing on uncertainty.
"""

from pathlib import Path

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, JobContext
from livekit.plugins import cartesia, deepgram, openai, silero

load_dotenv()

server = AgentServer()

PROMPT_PATH = Path(__file__).parent / "prompts" / "chat.txt"


class Assistant(Agent):
    def __init__(self) -> None:
        instructions = PROMPT_PATH.read_text(encoding="utf-8")
        super().__init__(instructions=instructions)


@server.rtc_session(agent_name="voiceagents-handbook-ch03")
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
    await session.generate_reply(instructions="Greet the caller warmly.")


if __name__ == "__main__":
    agents.cli.run_app(server)
