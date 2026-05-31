"""Mutating tool with disallow_interruptions and ToolError recovery.

The book_appointment tool always raises BookingAPIDown, so you can hear
what the agent does when a write fails. The ToolError message is written
as an instruction to the LLM, not a sentence to the caller. The LLM
rewrites it into something speakable.

Run:
    uv run python error_path.py dev
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
from livekit.agents.llm import ToolError
from livekit.plugins import cartesia, deepgram, openai, silero

load_dotenv()

server = AgentServer()


@dataclass
class CallData:
    callback_number: str | None = None


class SlotUnavailableError(Exception):
    pass


class BookingAPIDown(Exception):
    pass


async def _call_booking_api(service: str, requested_time: str):
    # Simulate a real outage. In a real system this would be a network
    # call to your dispatch backend.
    raise BookingAPIDown("Backend returned 503")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are answering the phone for ACME Plumbing. "
                "Speak the way a friendly receptionist speaks: short "
                "sentences, no lists. "
                "When the caller asks to book, use book_appointment. "
                "If a tool tells you the booking system is down, do exactly "
                "what the tool instruction says."
            )
        )

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
            await _call_booking_api(service, requested_time)
        except SlotUnavailableError:
            raise ToolError(
                "That time slot is no longer available. "
                "Offer the caller the next two available slots."
            )
        except BookingAPIDown:
            raise ToolError(
                "The booking system is temporarily unavailable. "
                "Offer to take the caller's number and call them back."
            )

        return "Booked."

    @function_tool()
    async def record_callback_number(
        self,
        context: RunContext[CallData],
        number: str,
    ) -> str:
        """Record a callback number when the caller gives one.

        Args:
            number: The phone number the caller said.
        """
        context.userdata.callback_number = number
        return f"Recorded callback number: {number}"


@server.rtc_session(agent_name="voiceagents-handbook-ch04")
async def error_path_agent(ctx: JobContext):
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
    await session.start(agent=Assistant(), room=ctx.room)
    await session.generate_reply(instructions="Greet the user warmly.")


if __name__ == "__main__":
    agents.cli.run_app(server)
