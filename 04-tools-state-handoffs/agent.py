"""ACME Plumbing: reception agent with pricing, booking, and handoff to billing.

Chapter 4 hero. Function tools, typed userdata, and one handoff.

Run:
    uv run python agent.py dev
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
from livekit.agents.llm import ToolError
from livekit.plugins import cartesia, deepgram, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()

server = AgentServer()


# ---------------------------------------------------------------------------
# Typed session state. Tools read and write to context.userdata.
# ---------------------------------------------------------------------------


@dataclass
class CallData:
    caller_name: str | None = None
    service_requested: str | None = None
    address: str | None = None
    quoted_price_usd: int | None = None


# ---------------------------------------------------------------------------
# Fake booking backend. Stand in for the real one your business already has.
# ---------------------------------------------------------------------------


class SlotUnavailableError(Exception):
    pass


class BookingAPIDown(Exception):
    pass


@dataclass
class Confirmation:
    id: str
    scheduled_for: str


PRICES = {
    "drain cleaning": 149,
    "leak repair": 199,
    "water heater install": 1450,
    "toilet replacement": 425,
}


async def _call_booking_api(service: str, requested_time: str) -> Confirmation:
    # In a real system this would hit your dispatch backend. The companion
    # repo keeps it in memory so the file runs without external setup.
    return Confirmation(id="ACME-10421", scheduled_for=requested_time)


# ---------------------------------------------------------------------------
# Reception agent. The default agent for inbound calls.
# ---------------------------------------------------------------------------


class ReceptionAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are answering the phone for ACME Plumbing. "
                "Speak the way a friendly receptionist speaks: short sentences, "
                "no lists, no markdown, no spelling things out. "
                "Handle general inquiries, pricing, and scheduling. "
                "When a caller asks about pricing, look it up with the "
                "get_service_price tool rather than guessing. "
                "When a caller asks to book, use book_appointment. "
                "If the caller has a billing question (payments, refunds, "
                "invoices, disputes), transfer to billing with "
                "transfer_to_billing."
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
        """Look up the price of a plumbing service.

        Args:
            service: The service the caller is asking about, for example
                "drain cleaning" or "water heater install".
        """
        price = PRICES.get(service.lower())
        if price is None:
            return {"found": False, "service": service}
        context.userdata.service_requested = service
        context.userdata.quoted_price_usd = price
        return {"found": True, "service": service, "price_usd": price}

    @function_tool()
    async def book_appointment(
        self,
        context: RunContext[CallData],
        service: str,
        requested_time: str,
    ) -> str:
        """Book an appointment for a plumbing service.

        Args:
            service: The service requested.
            requested_time: The time the caller wants, in plain language.
        """
        context.disallow_interruptions()

        try:
            confirmation = await _call_booking_api(service, requested_time)
        except SlotUnavailableError as err:
            raise ToolError(
                "That time slot is no longer available. "
                "Offer the caller the next two available slots."
            ) from err
        except BookingAPIDown as err:
            raise ToolError(
                "The booking system is temporarily unavailable. "
                "Offer to take the caller's number and call them back."
            ) from err

        context.userdata.service_requested = service
        return f"Booked: {confirmation.id}, {confirmation.scheduled_for}."

    @function_tool()
    async def transfer_to_billing(self, context: RunContext[CallData]):
        """Transfer the caller to a billing specialist."""
        return (
            BillingAgent(chat_ctx=self.chat_ctx.copy(exclude_instructions=True)),
            "Transferring to billing.",
        )


# ---------------------------------------------------------------------------
# Billing agent. The handoff target.
# ---------------------------------------------------------------------------


class BillingAgent(Agent):
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(
            instructions=(
                "You are a billing specialist at ACME Plumbing. "
                "Help callers with invoices, payments, and refunds. "
                "Speak briefly and warmly: short sentences, no lists, no "
                "markdown. If the caller asks about service pricing or "
                "scheduling, tell them you can hand them back to the front "
                "desk."
            ),
            chat_ctx=chat_ctx,
        )

    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions=("Introduce yourself briefly as billing, and ask how you can help.")
        )


# ---------------------------------------------------------------------------
# Entrypoint.
# ---------------------------------------------------------------------------


@server.rtc_session(agent_name="voiceagents-handbook-ch04")
async def acme_plumbing(ctx: JobContext):
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
    await session.start(agent=ReceptionAgent(), room=ctx.room)
    await session.generate_reply(instructions="Greet the user warmly.")


if __name__ == "__main__":
    agents.cli.run_app(server)
