"""Chapter 5 variant: adaptive interruption mode.

Adaptive mode uses an audio model trained to distinguish backchannels
("mm-hmm", "okay", "right") from real interruptions. It is the single most
impactful change for an agent that flinches every two sentences.

Four conditions must hold for adaptive mode to actually engage (section 5
of the chapter):

  1. Agent is deployed to LiveKit Cloud, or running in dev mode against it.
  2. VAD is enabled in the session.
  3. The LLM is not a realtime model.
  4. The STT model supports aligned transcripts (timestamps per word).
     Deepgram Nova-3 does. Check stt.capabilities.aligned_transcript for
     direct plugins.

If any condition is false, the framework silently falls back to VAD-only
interruption detection. No error, no warning. The "soft fallback" is the
trap: a reader who sets mode = "adaptive" while using a realtime LLM will
see no behavioral change and assume the feature is broken. It isn't; the
conditions just aren't met.
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
                "Walk the user through a short explanation of how a drain "
                "cleaning service call works, in two or three sentences. "
                "If the user says 'mm-hmm' or 'okay' while you're talking, "
                "keep going. If they say 'wait' or ask a real question, stop "
                "and respond to them. Do not use markdown."
            )
        )


server = AgentServer()


@server.rtc_session(agent_name="voiceagents-handbook-ch05")
async def my_agent(ctx: JobContext):
    await ctx.connect()
    session = AgentSession(
        turn_handling=TurnHandlingOptions(
            turn_detection=MultilingualModel(),
            interruption={
                "mode": "adaptive",
                # Half a second of detected speech before counting as an
                # interruption. Lower (0.3) for quiet or hesitant users.
                "min_duration": 0.5,
                # Default is 0; set to 2 to force a phrase before
                # interrupting (useful off LiveKit Cloud, where adaptive
                # mode silently downgrades to VAD-only).
                "min_words": 0,
                # The false-interruption safety net. If a presumed
                # interruption produces no transcript within this window,
                # the framework resumes the agent's speech.
                "false_interruption_timeout": 2.0,
                "resume_false_interruption": True,
            },
        ),
        # VAD is required for adaptive mode to engage.
        vad=silero.VAD.load(),
        # Deepgram Nova-3 produces aligned transcripts, which adaptive mode
        # needs. A model that does not would silently downgrade you.
        stt=deepgram.STT(model="nova-3"),
        # A non-realtime LLM is required for adaptive mode. gpt-4.1-mini is
        # non-realtime. A realtime model here would silently downgrade you.
        llm=openai.LLM(model="gpt-4.1-mini"),
        tts=cartesia.TTS(
            model="sonic-3",
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        ),
    )
    await session.start(agent=Assistant(), room=ctx.room)
    await session.generate_reply(
        instructions=(
            "Begin explaining how a drain cleaning service call works. "
            "Keep going if the user backchannels."
        )
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
