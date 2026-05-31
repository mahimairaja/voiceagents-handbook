"""Pattern 3: the triage agent.

A small, fast, short-lived agent whose only job is routing. It picks one of
three specialist agents and hands off the session. The triage agent itself
does not do the real work.

The book section: Chapter 6, Section 3.
"""

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    RunContext,
    function_tool,
)
from livekit.plugins import cartesia, deepgram, openai, silero

load_dotenv()

server = AgentServer()


class BillingAgent(Agent):
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(
            instructions=(
                "You handle billing questions for ACME Plumbing. "
                "Answer payment, invoice, and refund questions. "
                "If the caller asks for something outside billing, say so."
            ),
            chat_ctx=chat_ctx,
        )


class DispatchAgent(Agent):
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(
            instructions=(
                "You schedule plumber visits for ACME Plumbing. "
                "Collect the address, the problem, and a time window. "
                "Confirm the booking before ending the call."
            ),
            chat_ctx=chat_ctx,
        )


class EmergencyAgent(Agent):
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(
            instructions=(
                "You handle plumbing emergencies for ACME Plumbing. "
                "Stay calm. Gather the address and a short description. "
                "Tell the caller an on-call plumber will reach them shortly."
            ),
            chat_ctx=chat_ctx,
        )


class TriageAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are the front desk for ACME Plumbing. "
                "Listen for what the caller wants and route them. "
                "Do not attempt to help directly. Your only job is to route. "
                "Route within two or three turns. If the caller's intent is still "
                "unclear after that, hand off to dispatch rather than continuing "
                "to interrogate them."
            ),
        )

    @function_tool()
    async def to_billing(self, context: RunContext):
        """Route the caller to billing."""
        return (
            BillingAgent(chat_ctx=self.chat_ctx.copy(exclude_instructions=True)),
            "Connecting you to billing.",
        )

    @function_tool()
    async def to_dispatch(self, context: RunContext):
        """Route the caller to scheduling and dispatch."""
        return (
            DispatchAgent(chat_ctx=self.chat_ctx.copy(exclude_instructions=True)),
            "Getting a plumber on the line.",
        )

    @function_tool()
    async def to_emergency(self, context: RunContext):
        """Route the caller to the on-call emergency line."""
        return (
            EmergencyAgent(chat_ctx=self.chat_ctx.copy(exclude_instructions=True)),
            "Let me get you to our on-call.",
        )


@server.rtc_session(agent_name="voiceagents-handbook-ch06")
async def my_agent(ctx: JobContext):
    await ctx.connect()
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-3"),
        # A small, fast model is the right choice for triage. Anthropic Haiku 4.5
        # and Gemini 2.5 Flash-Lite are equally good. Stick to the book body's
        # default unless your triage prompt grows. See Appendix A for the
        # Haiku-for-tool-heavy callout.
        llm=openai.LLM(model="gpt-4.1-mini"),
        tts=cartesia.TTS(
            model="sonic-3",
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        ),
    )
    await session.start(agent=TriageAgent(), room=ctx.room)
    await session.generate_reply(
        instructions=(
            "Greet the caller as the ACME Plumbing front desk and ask how you can help today."
        )
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
