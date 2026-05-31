"""Branch on participant kind to adapt the session to the surface.

This is the corrected version of the example in Chapter 7 section 5.
The manuscript's printed example had both branches setting the same
STT model (a typo that made the branch tautological). The fix is to
genuinely pick different settings per surface:

- SIP (phone): narrowband-trained STT (Deepgram nova-2-phonecall),
  agent-side BVC noise cancellation enabled.
- STANDARD (browser or native mobile): full-bandwidth STT (Deepgram
  nova-3) with no extra noise cancellation; WebRTC's built-in
  suppression is already doing the work.

The 90% case is one agent with two or three small surface-aware
adjustments. Do not branch the whole agent into parallel codepaths.

Run with:
    uv run python surface_adaptation.py dev
"""

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import Agent, AgentServer, AgentSession, JobContext
from livekit.plugins import cartesia, deepgram, noise_cancellation, openai, silero

load_dotenv()

server = AgentServer()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a friendly receptionist for ACME Plumbing. "
                "Keep responses short. If the caller is on the phone, "
                "do not read URLs out loud; offer to text the link instead."
            )
        )


@server.rtc_session(agent_name="voiceagents-handbook-ch07")
async def my_agent(ctx: JobContext):
    await ctx.connect()
    participant = await ctx.wait_for_participant()

    is_phone = participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP

    if is_phone:
        # Phone caller: narrowband STT and agent-side BVCTelephony.
        # BVCTelephony is tuned for narrowband / 8 kHz SIP audio;
        # the wideband BVC() model would over-suppress phone speech.
        stt = deepgram.STT(model="nova-2-phonecall")
        input_options = agents.RoomInputOptions(
            noise_cancellation=noise_cancellation.BVCTelephony(),
        )
    else:
        # Browser or native mobile: full-bandwidth STT, no extra NC.
        stt = deepgram.STT(model="nova-3")
        input_options = agents.RoomInputOptions()

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=stt,
        llm=openai.LLM(model="gpt-4.1-mini"),
        tts=cartesia.TTS(
            model="sonic-3",
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        ),
    )
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=input_options,
    )

    greeting = "Greet the caller briefly." if is_phone else "Greet the user and offer to help."
    await session.generate_reply(instructions=greeting)


if __name__ == "__main__":
    agents.cli.run_app(server)
