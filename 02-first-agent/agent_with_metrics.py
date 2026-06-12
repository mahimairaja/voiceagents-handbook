from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    MetricsCollectedEvent,
    metrics,
)
from livekit.plugins import cartesia, deepgram, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a helpful voice assistant. "
                "Keep your responses short and conversational. "
                "Do not use markdown, lists, or headings. "
                "The user will hear this, not read it."
            )
        )


server = AgentServer()


@server.rtc_session(agent_name="voiceagents-handbook-ch02")
async def my_agent(ctx: JobContext):
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

    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics(event: MetricsCollectedEvent) -> None:
        metrics.log_metrics(event.metrics)
        usage_collector.collect(event.metrics)

        # Per-turn timing the chapter highlights.
        m = event.metrics
        if isinstance(m, metrics.LLMMetrics):
            print(f"[turn] LLM TTFT: {m.ttft * 1000:.0f} ms")
        elif isinstance(m, metrics.TTSMetrics):
            print(f"[turn] TTS time-to-first-audio: {m.ttfb * 1000:.0f} ms")
        elif isinstance(m, metrics.EOUMetrics):
            print(f"[turn] end-of-utterance delay: {m.end_of_utterance_delay * 1000:.0f} ms")

    async def _log_usage() -> None:
        summary = usage_collector.get_summary()
        print(f"[session] usage summary: {summary}")

    ctx.add_shutdown_callback(_log_usage)

    await session.start(agent=Assistant(), room=ctx.room)
    await session.generate_reply(instructions="Greet the user briefly.")


if __name__ == "__main__":
    agents.cli.run_app(server)
