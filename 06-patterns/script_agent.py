"""Pattern 5: the script agent.

A script agent reads. It does not converse. It reads a specific sequence of
statements (a recording-consent notice in this file) and only after the script
finishes does control yield to a conversational agent.

The defining property is that the script cannot be interrupted in the usual
sense. The user can speak; the framework will hear them. But the agent does
not stop reading until the script is done.

The book section: Chapter 6, Section 5.
"""

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, JobContext
from livekit.plugins import cartesia, deepgram, openai, silero

load_dotenv()

server = AgentServer()


class CustomerServiceAgent(Agent):
    """The conversational agent the script hands off to once the disclosure is done."""

    def __init__(self, chat_ctx=None) -> None:
        super().__init__(
            instructions=(
                "You are answering the phone for ACME Plumbing customer service. "
                "Acknowledge anything the caller said during the consent script "
                "by content, not just by tone. For example: 'Sorry, I needed to "
                "read that first. You were saying you wanted a quote?'"
            ),
            chat_ctx=chat_ctx,
        )


class ConsentScript(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You read a recording consent disclosure to callers.",
        )

    async def on_enter(self) -> None:
        # allow_interruptions=False on the per-call form. The disclosure must
        # complete. The conversational agent that follows is normally
        # interruptible.
        await self.session.say(
            "This call may be recorded for quality and training purposes. "
            "If you do not consent, please hang up now. "
            "Otherwise, please stay on the line.",
            allow_interruptions=False,
        )
        # Yield to the conversational agent. on_enter does not return-as-handoff
        # the way a function_tool does; use update_agent explicitly.
        self.session.update_agent(
            CustomerServiceAgent(chat_ctx=self.chat_ctx.copy(exclude_instructions=True))
        )


@server.rtc_session(agent_name="voiceagents-handbook-ch06")
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
    await session.start(agent=ConsentScript(), room=ctx.room)


if __name__ == "__main__":
    agents.cli.run_app(server)
