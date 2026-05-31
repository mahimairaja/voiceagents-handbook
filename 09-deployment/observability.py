"""OpenTelemetry adapter: turn `metrics_collected` events into OTLP spans.

This is a reference adapter, not a live deployment. Point
OTEL_EXPORTER_OTLP_ENDPOINT at your collector (Honeycomb, Grafana Cloud, a
local otel-collector via docker-compose.yml) and per-session spans land in
your existing observability stack.

What it exports:
- One root span per session (`voiceagent.session`), attributed with the room
  name and session id.
- One child span per metric event (STTMetrics, LLMMetrics, TTSMetrics, EOUMetrics).
  Each child carries the metric payload as span attributes so you can filter,
  group, and chart per-provider latency in Honeycomb or Tempo.

Run locally with:
    docker-compose up otel-collector  # in another shell
    uv run python observability.py dev
"""

from __future__ import annotations

import os
import time
import uuid
from contextlib import suppress

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    metrics,
)
from livekit.plugins import cartesia, deepgram, openai, silero
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

load_dotenv()


def _configure_tracer() -> trace.Tracer:
    """Set up the global tracer provider if OTEL_EXPORTER_OTLP_ENDPOINT is set."""
    resource = Resource.create({SERVICE_NAME: "voiceagents-handbook-ch09"})
    provider = TracerProvider(resource=resource)

    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        # The exporter picks up endpoint + headers from OTEL_* env vars.
        exporter = OTLPSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
    return trace.get_tracer("voiceagents-handbook-ch09")


tracer = _configure_tracer()
server = AgentServer()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a friendly voice assistant. Speak in short sentences."
        )


@server.rtc_session(agent_name="voiceagents-handbook-ch09")
async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    session_id = str(uuid.uuid4())
    session_span = tracer.start_span("voiceagent.session")
    session_span.set_attribute("session.id", session_id)
    session_span.set_attribute("room.name", ctx.room.name)
    session_start = time.time()

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-3"),
        llm=openai.LLM(model="gpt-4.1-mini"),
        tts=cartesia.TTS(
            model="sonic-3",
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        ),
    )

    @session.on("metrics_collected")
    def _on_metrics(ev: metrics.MetricsCollectedEvent) -> None:
        metric = ev.metrics
        with tracer.start_as_current_span(f"voiceagent.{type(metric).__name__}") as span:
            span.set_attribute("session.id", session_id)
            for key, value in _flatten_metric(metric).items():
                with suppress(Exception):
                    span.set_attribute(f"metric.{key}", value)

    async def close_session_span() -> None:
        session_span.set_attribute("session.duration_seconds", time.time() - session_start)
        session_span.end()

    ctx.add_shutdown_callback(close_session_span)

    await session.start(agent=Assistant(), room=ctx.room)
    await session.generate_reply(instructions="Greet the user warmly.")


def _flatten_metric(metric: object) -> dict[str, float | int | str | bool]:
    """Reduce a metric object to OTLP-compatible attribute values."""
    raw: dict[str, object] = {}
    if hasattr(metric, "model_dump"):
        raw = metric.model_dump()
    elif hasattr(metric, "__dict__"):
        raw = {k: v for k, v in metric.__dict__.items() if not k.startswith("_")}

    flat: dict[str, float | int | str | bool] = {}
    for key, value in raw.items():
        if isinstance(value, (int, float, str, bool)):
            flat[key] = value
        elif value is None:
            continue
        else:
            flat[key] = str(value)
    return flat


if __name__ == "__main__":
    agents.cli.run_app(server)
