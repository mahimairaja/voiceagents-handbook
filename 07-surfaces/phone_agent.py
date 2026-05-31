"""SIP-tuned agent variant for phone callers.

Differences from the surface-agnostic baseline in agent.py:

1. The STT model is Deepgram's nova-2-phonecall variant, trained on
   narrowband telephony audio (8 kHz G.711) rather than full-bandwidth
   browser audio.
2. Agent-side noise cancellation (BVC) is enabled on the input audio
   so background noise from the caller's environment is suppressed
   before STT sees it. This stacks with trunk-level Krisp; ship both.
3. The prompt nudges the agent to verbally signal slow work and to
   confirm understanding explicitly, since the caller cannot see a
   "thinking" indicator or a transcription pane.

Wire this agent to a SIP inbound trunk and dispatch rule (see trunk/
in this folder) and the agent picks up phone calls.

Run with:
    uv run python phone_agent.py dev
"""

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, JobContext
from livekit.plugins import cartesia, deepgram, noise_cancellation, openai, silero

load_dotenv()

server = AgentServer()


class PhoneAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a phone receptionist for ACME Plumbing. "
                "The caller can only hear you; they cannot see anything. "
                "When you need to look something up, say 'let me check that' "
                "before you do. Confirm names and numbers out loud by "
                "repeating them back. End the call with a clear goodbye."
            )
        )


@server.rtc_session(agent_name="voiceagents-handbook-ch07")
async def my_agent(ctx: JobContext):
    await ctx.connect()
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-2-phonecall"),
        llm=openai.LLM(model="gpt-4.1-mini"),
        tts=cartesia.TTS(
            model="sonic-3",
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        ),
    )
    await session.start(
        agent=PhoneAssistant(),
        room=ctx.room,
        room_input_options=agents.RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    await session.generate_reply(
        instructions=("Greet the caller briefly. Ask how you can help. Keep it under ten words.")
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
