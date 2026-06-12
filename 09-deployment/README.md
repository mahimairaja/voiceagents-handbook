# Chapter 9: Deployment and Observability

Ship the agent: a deployable voice agent, a production-shaped Dockerfile, prewarming, OTLP traces, and a SIGTERM-respecting drain script.

## What this folder contains

- `agent.py`: the hero agent. Greeting, one `function_tool`, and a `metrics_collected` listener that writes per-session JSONL to `./session-metrics/`.
- `prewarm.py`: the prewarm pattern. Loads silero VAD and the multilingual turn-detector once per worker via `server.setup_fnc`.
- `observability.py`: OTLP adapter. Turns `metrics_collected` events into OpenTelemetry spans you can ship to Honeycomb, Grafana Cloud, or a local collector.
- `quality_eval.py`: the production half of the Chapter 8 test loop. Runs `JudgeGroup` (accuracy, relevancy, safety, task-completion) against the live transcript on the session shutdown callback.
- `Dockerfile`: production-shaped image (python:3.11-slim, uv sync from the committed lockfile, non-root user, model files baked in).
- `docker-compose.yml`: brings up the agent plus an optional otel-collector for local trace exploration.
- `drain.sh`: graceful SIGTERM-then-wait-then-SIGKILL drain compatible with hour-long sessions.
- `livekit.toml`: LiveKit Cloud deploy config. It identifies the project and agent only; regions, autoscaling, and prewarm count are dashboard settings, not file keys (the comments in the file say where each one lives).

## Setup

Prerequisites: Python 3.11+, uv, Docker (for the container and compose flows), accounts with LiveKit Cloud, Deepgram, OpenAI, and Cartesia. The OTLP variables are optional; leave them blank if you do not have a collector yet.

```bash
cp .env.example .env
# Fill in keys
uv sync
```

## Run

Locally, the same flow as every other chapter:

```bash
uv run python agent.py dev
```

To exercise the prewarm pattern:

```bash
uv run python prewarm.py dev
```

To export OTLP spans, set `OTEL_EXPORTER_OTLP_ENDPOINT` in `.env`, then:

```bash
uv run python observability.py dev
```

To judge every conversation as it ends (quality eval on the shutdown callback):

```bash
uv run python quality_eval.py dev
```

### Run with Docker Compose

```bash
docker compose up --build
```

The `agent` service starts in `start` mode (production) and exposes the health-check port on `8081`. It runs `agent.py`, which logs metrics to JSONL; it does not emit OTLP traces on its own. To forward traces, run the OTLP variant (`observability.py`) as the container command, or set `OTEL_EXPORTER_OTLP_ENDPOINT` and run `observability.py` locally. The optional `otel-collector` service (enable with `docker compose --profile otel up`) gives you a local endpoint; provide an `otel-collector-config.yaml` next to `docker-compose.yml` to route those traces to your real backend.

### Deploy to LiveKit Cloud

Once `lk` is installed and authenticated:

```bash
lk agent create   # first deploy
lk agent deploy   # subsequent deploys
```

`livekit.toml` in this folder is the config the CLI reads. `lk agent create` fills in the project subdomain and agent id for you. Regions, autoscaling, and prewarm count are not keys in this file; set them in the LiveKit Cloud dashboard (the file's comments point to each one).

### Drain a self-hosted worker

```bash
./drain.sh <pid>
# or
LIVEKIT_DRAIN_TIMEOUT=900 ./drain.sh <pid>
```

The script sends SIGTERM, waits up to `LIVEKIT_DRAIN_TIMEOUT` seconds (default 600) for in-flight sessions to finish, then SIGKILLs as a last resort.

## What to listen for

- After a cold start with `agent.py`, the first reply takes a noticeable beat: model weights are loading.
- After a cold start with `prewarm.py`, the first reply is fast: weights were loaded before the call.
- `./session-metrics/<session-id>.jsonl` fills in real time. Each line is one metric event; the last line is the session summary.

## Variations

| File | What it does | Book section |
| ---- | ------------ | ------------ |
| `agent.py` | Deployable agent with tool and per-session metrics log | Section 2, 5 |
| `prewarm.py` | Prewarm hook for VAD and turn detector | Section 4 |
| `observability.py` | OTLP span exporter wrapping `metrics_collected` | Section 5 |
| `quality_eval.py` | `JudgeGroup` quality eval on the session shutdown callback | Section 5 |
| `Dockerfile` | Production-shaped container image | Section 2 |
| `docker-compose.yml` | Local stack with agent and OTLP collector | Section 5 |
| `drain.sh` | SIGTERM-respecting drain for hour-long sessions | Section 6 |
| `livekit.toml` | LiveKit Cloud deploy config (project + agent id) | Section 2 |

## See also

Chapter 9 of *Voice Agents Handbook* by Mahimai Raja J. ASIN B0FJ7Q96H1.
