# Voice Agents Handbook: Code

The code companion to *Voice Agents Handbook: Building Production Voice AI with LiveKit* by Mahimai Raja J. Kindle: [amazon.com/dp/B0FJ7Q96H1](https://www.amazon.com/dp/B0FJ7Q96H1). Site: [handbook.mahimai.ca](https://handbook.mahimai.ca).

Each chapter folder is a hermetic [uv](https://docs.astral.sh/uv/) project. Clone, cd into the chapter you're reading, fill in your keys, and run.

## Get the keys

You'll need a LiveKit Cloud account and accounts with three to five providers depending on which chapters you run. Most chapters only need the first four rows.

| Provider | Signup | Env var | Used in |
| -------- | ------ | ------- | ------- |
| LiveKit Cloud | [cloud.livekit.io](https://cloud.livekit.io) | `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` | every chapter |
| Deepgram | [console.deepgram.com](https://console.deepgram.com) | `DEEPGRAM_API_KEY` | every chapter |
| OpenAI | [platform.openai.com](https://platform.openai.com) | `OPENAI_API_KEY` | every chapter |
| Cartesia | [play.cartesia.ai](https://play.cartesia.ai) | `CARTESIA_API_KEY` | every chapter |
| Anthropic | [console.anthropic.com](https://console.anthropic.com) | `ANTHROPIC_API_KEY` | Ch 4 (optional), Ch 6 |
| Google AI | [aistudio.google.com](https://aistudio.google.com) | `GOOGLE_API_KEY` | Ch 6 (triage variants) |
| AssemblyAI | [assemblyai.com](https://www.assemblyai.com) | `ASSEMBLYAI_API_KEY` | Ch 7 (phone-tuned STT) |
| OTLP collector | your choice (Honeycomb, Grafana Cloud, ...) | `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_HEADERS` | Ch 9 (optional) |

Each chapter ships its own `.env.example` listing only the keys it uses. Copy it to `.env` and fill in what's needed.

## Chapter index

| Folder | Chapter | What you'll run |
| ------ | ------- | --------------- |
| [`01-voice-stack/`](./01-voice-stack/) | Chapter 1: The Voice Agent Stack on LiveKit | The 30-line baseline agent (Inference + MultilingualModel) |
| [`02-first-agent/`](./02-first-agent/) | Chapter 2: Your First Agent | The 40-line working agent and a metrics-printing variant |
| [`03-prompts/`](./03-prompts/) | Chapter 3: Prompts for Voice | Voice-shaped vs chat-shaped prompts side by side |
| [`04-tools-state-handoffs/`](./04-tools-state-handoffs/) | Chapter 4: Function Tools, State, and Handoffs | ACME plumbing booking agent plus four isolated patterns |
| [`05-latency-turn-taking/`](./05-latency-turn-taking/) | Chapter 5: Latency, Interruptions, and Turn-Taking | Tuned baseline plus three timing failure-mode demos |
| [`06-patterns/`](./06-patterns/) | Chapter 6: Common Patterns | Six runnable patterns (triage, script, observer, router, outbound, survey) |
| [`07-surfaces/`](./07-surfaces/) | Chapter 7: Surfaces | Phone-tuned agent, surface adaptation, SIP trunk config |
| [`08-testing/`](./08-testing/) | Chapter 8: Testing with Synthetic Callers | Pytest suite with conftest fixtures and JudgeGroup examples |
| [`09-deployment/`](./09-deployment/) | Chapter 9: Deployment and Observability | Dockerfile, compose, prewarm, drain, OTLP observability |

For the browser and mobile client code Chapter 7 walks through, point [`livekit-examples/voice-pipeline-frontend`](https://github.com/livekit-examples/voice-pipeline-frontend) (web) or the React Native equivalent at the agent name registered in `07-surfaces/agent.py`.

## How to use this repo

```bash
git clone https://github.com/mahimairaja/voiceagents-handbook
cd voiceagents-handbook/02-first-agent

cp .env.example .env       # fill in your keys
uv sync                    # pulls livekit-agents and chapter-specific plugins
uv run python agent.py dev # LiveKit Agents CLI dev mode
```

Then dial your agent over the LiveKit playground or the [voice-pipeline-frontend](https://github.com/livekit-examples/voice-pipeline-frontend) starter. The chapter README tells you what to listen for.

## Tag policy

- `book-v1` is the frozen state of this repo at the June 2026 print launch. Check this tag out if you want the print-edition code.
- `main` tracks current `livekit-agents` releases. Subsequent tags (`book-v1.1`, `book-v2`, ...) document changes since print in release notes.

## License

MIT. See [LICENSE](./LICENSE).

## Errata and contributing

Book corrections live in [`docs/ERRATA.md`](./docs/ERRATA.md). Repo bugs, provider drift, and contributions go through [`docs/CONTRIBUTING.md`](./docs/CONTRIBUTING.md).
