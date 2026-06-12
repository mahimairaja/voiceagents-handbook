"""ACME Plumbing agent used as the unit under test for Chapter 8.

Run with `uv run python agent.py dev` to talk to it through the LiveKit
playground. Run with `uv run pytest` to exercise it through the synthetic
caller framework in `tests/`.
"""

from __future__ import annotations

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


INSTRUCTIONS = (
    "You are the receptionist at ACME Plumbing, a small family-run plumbing "
    "business. Greet callers warmly and offer to help. When a caller asks for "
    "a price, call get_service_price to look it up, then quote the price in "
    "words rather than digits. When a caller wants to book a visit, call "
    "book_appointment with the service name and requested time. Never read out "
    "URLs or website addresses. Keep responses short and conversational."
)


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=INSTRUCTIONS)

    @function_tool
    async def get_service_price(self, context: RunContext, service: str) -> str:
        """Look up the price for a named plumbing service.

        Args:
            service: The name of the service, for example "drain cleaning".
        """
        prices = {
            "drain cleaning": "one forty-nine",
            "leak repair": "two twenty-nine",
            "water heater install": "nine hundred",
        }
        key = service.strip().lower()
        if key in prices:
            return f"The price for {service} is {prices[key]} dollars."
        return f"We don't have a flat rate for {service}; a technician will quote on site."

    @function_tool
    async def book_appointment(
        self,
        context: RunContext,
        service: str,
        requested_time: str,
    ) -> str:
        """Book a plumbing visit.

        Args:
            service: The service the caller wants, for example "drain cleaning".
            requested_time: A human-readable time, for example "Thursday at 3 PM".
        """
        return f"Confirmed: {service} on {requested_time}."


@server.rtc_session(agent_name="voiceagents-handbook-ch08")
async def acme_plumbing(ctx: JobContext):
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
    await session.generate_reply(instructions="Greet the caller warmly and offer to help.")


if __name__ == "__main__":
    agents.cli.run_app(server)
