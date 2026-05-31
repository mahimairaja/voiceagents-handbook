"""Pattern 2: the survey agent.

A survey agent has a known terminal state: the moment when a specific set of
fields has been collected. Name. Address. Symptoms. Once the fields are full,
the agent is done. The conversation is open-ended in how the information is
collected, but closed in what must be collected before the agent can move on.

The difference between a survey agent and a conversational agent with a long
prompt that says 'make sure to collect name, phone, address' is the check. A
conversational agent might forget to ask. A survey agent cannot complete
without it.

The book section: Chapter 6, Section 2.
"""

from dataclasses import dataclass

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    AgentTask,
    JobContext,
    RunContext,
    function_tool,
)
from livekit.plugins import cartesia, deepgram, openai, silero

load_dotenv()

server = AgentServer()


@dataclass
class IntakeResult:
    name: str
    phone: str
    address: str
    symptoms: str


class IntakeTask(AgentTask[IntakeResult]):
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(
            instructions=(
                "Collect the caller's name, phone number, address, and a short "
                "description of the plumbing symptoms. Ask one field at a time. "
                "Read the address back to confirm it."
            ),
            chat_ctx=chat_ctx,
        )
        self._fields: dict[str, str] = {}

    @function_tool()
    async def record_name(self, context: RunContext, name: str) -> str:
        """Record the caller's name."""
        self._fields["name"] = name
        self._check_complete()
        return f"Got the name as {name}."

    @function_tool()
    async def record_phone(self, context: RunContext, phone: str) -> str:
        """Record the caller's phone number."""
        self._fields["phone"] = phone
        self._check_complete()
        return f"Got the phone as {phone}."

    @function_tool()
    async def record_address(self, context: RunContext, address: str) -> str:
        """Record the caller's service address."""
        self._fields["address"] = address
        self._check_complete()
        return f"Got the address as {address}."

    @function_tool()
    async def record_symptoms(self, context: RunContext, symptoms: str) -> str:
        """Record a short description of the plumbing problem."""
        self._fields["symptoms"] = symptoms
        self._check_complete()
        return f"Got the symptoms as {symptoms}."

    def _check_complete(self) -> None:
        required = {"name", "phone", "address", "symptoms"}
        if set(self._fields.keys()) == required:
            self.complete(IntakeResult(**self._fields))


class IntakeAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You run an intake for ACME Plumbing. Start the intake task "
                "immediately after greeting the caller. Once the task completes, "
                "thank the caller and confirm next steps."
            )
        )

    async def on_enter(self) -> None:
        await self.session.say("Hi, this is ACME Plumbing intake. I'll ask a few quick questions.")
        result = await IntakeTask(chat_ctx=self.chat_ctx).run()
        await self.session.say(
            f"Thanks {result.name}. A plumber will reach you at {result.phone} "
            f"to confirm the visit to {result.address}."
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
    # IntakeAgent.on_enter owns the first turn (greeting plus the start of
    # the intake task). Do not also call session.generate_reply here, or the
    # caller will hear two opening prompts overlap.
    await session.start(agent=IntakeAgent(), room=ctx.room)


if __name__ == "__main__":
    agents.cli.run_app(server)
