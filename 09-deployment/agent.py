"""Chapter 9 hero agent: a deployable voice agent with a tool and per-session metrics.

What this file demonstrates:
- A complete agent ready to ship behind the Dockerfile in this folder.
- One `function_tool` so deploys carry a non-trivial code path.
- A `metrics_collected` listener that writes a per-session JSON event log to
  ./session-metrics/<session-id>.jsonl. In production, ship this log to your
  observability stack (see observability.py for an OTLP variant).

Run locally with:
    uv sync
    uv run python agent.py dev
"""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    RunContext,
    function_tool,
    metrics,
)
from livekit.plugins import cartesia, deepgram, openai, silero

load_dotenv()

server = AgentServer()

METRICS_DIR = Path(os.getenv("SESSION_METRICS_DIR", "./session-metrics"))


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a friendly voice assistant for ACME Plumbing. "
                "Greet callers warmly, ask how you can help, and offer to look up "
                "appointment availability when callers want to book service. "
                "Speak in short sentences. Never read URLs or markdown out loud."
            )
        )

    @function_tool
    async def get_next_available_slot(self, context: RunContext) -> dict:
        """Return the next available service appointment slot.

        Use this when the caller asks about scheduling, availability, or when
        they want to book a plumber visit.
        """
        return {
            "slot_id": "slot-001",
            "starts_at": "2026-06-02T09:00:00-04:00",
            "duration_minutes": 60,
            "technician": "Jordan",
        }


@server.rtc_session(agent_name="voiceagents-handbook-ch09")
async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    session_id = str(uuid.uuid4())
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    metrics_file = METRICS_DIR / f"{session_id}.jsonl"

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-3"),
        llm=openai.LLM(model="gpt-4.1-mini"),
        tts=cartesia.TTS(
            model="sonic-3",
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        ),
    )

    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics(ev: metrics.MetricsCollectedEvent) -> None:
        # Log to console for local development.
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)
        # Write a JSONL line per metric event for downstream processing.
        record = {
            "session_id": session_id,
            "room": ctx.room.name,
            "timestamp": time.time(),
            "metric_type": type(ev.metrics).__name__,
            "data": _metrics_to_dict(ev.metrics),
        }
        with metrics_file.open("a") as fh:
            fh.write(json.dumps(record) + "\n")

    async def log_session_summary() -> None:
        summary = usage_collector.get_summary()
        record = {
            "session_id": session_id,
            "room": ctx.room.name,
            "timestamp": time.time(),
            "metric_type": "SessionSummary",
            "data": _metrics_to_dict(summary),
        }
        with metrics_file.open("a") as fh:
            fh.write(json.dumps(record) + "\n")

    ctx.add_shutdown_callback(log_session_summary)

    await session.start(agent=Assistant(), room=ctx.room)
    await session.generate_reply(
        instructions="Greet the caller warmly and ask how you can help today."
    )


def _metrics_to_dict(obj: object) -> dict:
    """Best-effort serializer for LiveKit metric objects."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return {"value": str(obj)}


if __name__ == "__main__":
    agents.cli.run_app(server)
