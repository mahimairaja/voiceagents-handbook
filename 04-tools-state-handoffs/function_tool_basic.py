"""Minimal function tool example.

One tool, one docstring, one return value. Ask the agent "how much for a
drain cleaning?" and listen for the brief pause while the tool runs.

Run:
    uv run python function_tool_basic.py dev
"""

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


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are answering the phone for ACME Plumbing. "
                "Speak the way a friendly receptionist speaks: short "
                "sentences, no lists, no markdown. "
                "When a caller asks about pricing, look it up with the "
                "get_service_price tool rather than guessing."
            )
        )

    @function_tool()
    async def get_service_price(
        self,
        context: RunContext,
        service: str,
    ) -> dict[str, Any]:
        """Look up the price of a plumbing service.

        Args:
            service: The service the caller is asking about, for example
                "drain cleaning" or "water heater install".
        """
        prices = {
            "drain cleaning": 149,
            "leak repair": 199,
            "water heater install": 1450,
            "toilet replacement": 425,
        }
        price = prices.get(service.lower())
        if price is None:
            return {"found": False, "service": service}
        return {"found": True, "service": service, "price_usd": price}


@server.rtc_session(agent_name="voiceagents-handbook-ch04")
async def basic_tool(ctx: JobContext):
    await ctx.connect()
    session = AgentSession(
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
