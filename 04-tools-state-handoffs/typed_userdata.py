"""Typed userdata as the per-session spine.

Two tools share a CallData dataclass across turns. The pricing tool writes
to context.userdata, and a later tool reads from it without asking the
caller to repeat themselves.

Run:
    uv run python typed_userdata.py dev
"""

from dataclasses import dataclass
from typing import Any

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
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()

server = AgentServer()


@dataclass
class CallData:
    caller_name: str | None = None
    service_requested: str | None = None
    quoted_price_usd: int | None = None


PRICES = {
    "drain cleaning": 149,
    "leak repair": 199,
    "water heater install": 1450,
    "toilet replacement": 425,
}


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are answering the phone for ACME Plumbing. "
                "Speak the way a friendly receptionist speaks: short "
                "sentences, no lists, no markdown. "
                "When the caller introduces themselves, call "
                "record_caller_name with their name. "
                "When the caller asks about pricing, call get_service_price. "
                "When the caller asks to confirm what was quoted, call "
                "summarize_quote."
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
            name: The caller's name, as they said it.
        """
        context.userdata.caller_name = name
        return f"Recorded caller name: {name}"

    @function_tool()
    async def get_service_price(
        self,
        context: RunContext[CallData],
        service: str,
    ) -> dict[str, Any]:
        """Look up the price of a plumbing service and remember the quote.

        Args:
            service: The service the caller is asking about.
        """
        price = PRICES.get(service.lower())
        if price is None:
            return {"found": False, "service": service}
        context.userdata.service_requested = service
        context.userdata.quoted_price_usd = price
        return {"found": True, "service": service, "price_usd": price}

    @function_tool()
    async def summarize_quote(
        self,
        context: RunContext[CallData],
    ) -> dict[str, Any]:
        """Summarize what was quoted to the caller so far."""
        data = context.userdata
        return {
            "caller_name": data.caller_name,
            "service_requested": data.service_requested,
            "quoted_price_usd": data.quoted_price_usd,
        }


@server.rtc_session(agent_name="voiceagents-handbook-ch04")
async def typed_userdata_agent(ctx: JobContext):
    await ctx.connect()
    session = AgentSession[CallData](
        userdata=CallData(),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
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
