"""Pattern 6: the outbound agent.

An outbound agent initiates the call rather than receiving it. It dials a
number, waits for someone to answer, and then runs a conversation.

The lifecycle has four concerns the inbound case does not have:
1. You dispatch the agent yourself rather than waiting for a room to be created.
2. You create a SIP participant to dial the number.
3. You wait for the callee to answer before starting the session.
4. You handle the cases where they do not answer (busy, voicemail, no-answer).

The detail that catches everyone the first time: do not have the agent speak
first on an outbound call. The callee just picked up. They will say 'hello'.
That utterance is the cue the agent should respond to.

The book section: Chapter 6, Section 6.

To dispatch this agent:
    lk dispatch create \\
        --agent-name voiceagents-handbook-ch06 \\
        --room outbound-test \\
        --metadata '{"phone_number": "+15551234567"}'
"""

import json
import logging
import os

from dotenv import load_dotenv
from livekit import agents, api
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
)
from livekit.plugins import cartesia, deepgram, openai, silero

load_dotenv()

logger = logging.getLogger("outbound_caller")
logger.setLevel(logging.INFO)

server = AgentServer()


class OutboundAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are calling on behalf of ACME Plumbing to confirm an "
                "appointment for tomorrow morning. The callee will speak first. "
                "Wait for them, then introduce yourself and confirm the time."
            )
        )


@server.rtc_session(agent_name="voiceagents-handbook-ch06")
async def my_agent(ctx: JobContext):
    await ctx.connect()

    # The phone number to dial arrives in the job metadata. Dispatch with:
    #   lk dispatch create --agent-name voiceagents-handbook-ch06 \
    #       --metadata '{"phone_number": "+15551234567"}'
    dial_info = json.loads(ctx.job.metadata or "{}")
    phone_number = dial_info.get("phone_number")
    if not phone_number:
        logger.error("no phone_number in job metadata; nothing to dial")
        ctx.shutdown()
        return

    sip_trunk_id = os.environ.get("SIP_OUTBOUND_TRUNK_ID")
    if not sip_trunk_id:
        logger.error("SIP_OUTBOUND_TRUNK_ID not set; cannot dial out")
        ctx.shutdown()
        return

    try:
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=sip_trunk_id,
                sip_call_to=phone_number,
                participant_identity=phone_number,
                wait_until_answered=True,
            )
        )
    except api.TwirpError as exc:
        sip_code = exc.metadata.get("sip_status_code") if exc.metadata else None
        logger.error("call failed (SIP %s): %s", sip_code, exc.message)
        ctx.shutdown()
        return

    participant = await ctx.wait_for_participant(identity=phone_number)

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-3"),
        llm=openai.LLM(model="gpt-4.1-mini"),
        tts=cartesia.TTS(
            model="sonic-3",
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        ),
    )
    await session.start(
        agent=OutboundAssistant(),
        room=ctx.room,
        participant=participant,
    )
    # Do not greet first. Wait for the callee to speak. The omitted
    # generate_reply() call is the entire reason this feels like a human call
    # and not a robocall.


if __name__ == "__main__":
    agents.cli.run_app(server)
