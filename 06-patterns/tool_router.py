"""Pattern 1: the conversational agent.

One user, one agent, open-ended dialog, tools to make the agent useful, prompts
to make it sound right. This file shows the conversational pattern in its
tool-rich form: one agent, many function tools, the tools do the actual work.

The book section: Chapter 6, Section 1.

The failure mode of conversational agents is scope creep. The prompt grows,
the tools multiply, and the agent ends up trying to do five jobs badly. If the
system prompt grows past fifty lines, split into specialists (see agent.py for
the triage variant) or pull the structured outcomes out into a survey agent
(see survey_agent.py).
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


# A small price book the tools query. In production this is a database call.
SERVICE_PRICES = {
    "drain cleaning": 149.0,
    "leak repair": 199.0,
    "water heater install": 1499.0,
    "toilet replacement": 349.0,
}


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are answering the phone for ACME Plumbing. "
                "Help callers find pricing, check availability for a visit, and "
                "explain what work would be involved. Speak naturally. Confirm "
                "numbers and addresses by reading them back. Keep your answers "
                "short enough to listen to."
            ),
        )

    @function_tool()
    async def get_service_price(self, context: RunContext, service: str) -> str:
        """Look up the price of a plumbing service.

        Args:
            service: The name of the service, like 'drain cleaning' or 'leak repair'.
        """

        key = service.lower().strip()
        price = SERVICE_PRICES.get(key)
        if price is None:
            return f"No standard price for {service}. A plumber will need to quote it on site."
        return f"{service} is {price:.2f} dollars."

    @function_tool()
    async def check_availability(self, context: RunContext, day: str) -> str:
        """Check whether a plumber is available on the given day.

        Args:
            day: The day to check, like 'Monday' or 'tomorrow'.
        """

        # In production this calls the scheduling system. The shape of the
        # answer matters: speak it the way a person would.
        return f"We have a window on {day} between nine and eleven in the morning."

    @function_tool()
    async def list_services(self, context: RunContext) -> str:
        """List the plumbing services ACME offers with prices."""

        return ", ".join(f"{name} at {price:.2f} dollars" for name, price in SERVICE_PRICES.items())


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
    await session.start(agent=Assistant(), room=ctx.room)
    await session.generate_reply(instructions="Greet the caller warmly.")


if __name__ == "__main__":
    agents.cli.run_app(server)
