"""Handoff pattern: reception agent transfers to billing agent.

The transfer_to_billing tool returns a tuple of (new_agent, short_message).
chat_ctx.copy(exclude_instructions=True) carries the conversation history
forward without dragging the previous agent's system prompt along.

Run:
    uv run python handoff_pattern.py dev
"""

from dataclasses import dataclass

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


@dataclass
class CallData:
    caller_name: str | None = None


class ReceptionAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are answering the phone for ACME Plumbing. "
                "Speak the way a friendly receptionist speaks: short "
                "sentences, no lists. "
                "If the caller introduces themselves, call record_caller_name. "
                "If the caller has a billing question (payments, refunds, "
                "invoices, disputes), call transfer_to_billing."
            )
        )

    @function_tool()
    async def record_caller_name(
        self,
        context: RunContext[CallData],
        name: str,
    ) -> str:
        """Record the caller's name when they introduce themselves.

        Args:
            name: The caller's name.
        """
        context.userdata.caller_name = name
        return f"Recorded caller name: {name}"

    @function_tool()
    async def transfer_to_billing(self, context: RunContext[CallData]):
        """Transfer the caller to a billing specialist."""
        return (
            BillingAgent(chat_ctx=self.chat_ctx.copy(exclude_instructions=True)),
            "Transferring to billing.",
        )


class BillingAgent(Agent):
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(
            instructions=(
                "You are a billing specialist at ACME Plumbing. "
                "Help callers with invoices, payments, and refunds. "
                "Speak briefly and warmly: short sentences, no lists. "
                "If the caller asks about service pricing or scheduling, "
                "tell them you can hand them back to the front desk."
            ),
            chat_ctx=chat_ctx,
        )

    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions=(
                "Introduce yourself briefly as billing, and ask how you can help."
            )
        )


@server.rtc_session(agent_name="voiceagents-handbook-ch04")
async def handoff_agent(ctx: JobContext):
    await ctx.connect()
    session = AgentSession[CallData](
        userdata=CallData(),
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-3"),
        llm=openai.LLM(model="gpt-4.1-mini"),
        tts=cartesia.TTS(
            model="sonic-3",
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        ),
    )
    await session.start(agent=ReceptionAgent(), room=ctx.room)
    await session.generate_reply(instructions="Greet the user warmly.")


if __name__ == "__main__":
    agents.cli.run_app(server)
