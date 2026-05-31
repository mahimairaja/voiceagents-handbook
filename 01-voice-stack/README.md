# Chapter 1: The Voice Agent Stack on LiveKit

The thirty-line baseline agent that names every component the rest of the book builds on.

## What this folder contains

- `agent.py`: minimal `AgentSession` wiring Silero VAD, Deepgram Nova-3 STT, OpenAI gpt-4.1-mini, and Cartesia Sonic-3 TTS into a single LiveKit agent registered as `voiceagents-handbook-ch01`.

## Setup

Prerequisites: Python 3.11+, uv, accounts with LiveKit Cloud, Deepgram, OpenAI, and Cartesia.

```bash
cp .env.example .env
# Fill in keys
uv sync
```

## Run

```bash
uv run python agent.py dev
```

Connect to the dev session at https://agents-playground.livekit.io and pick the LiveKit project tied to your `LIVEKIT_URL`. The agent greets you the moment the room connects.

## What to listen for

- First audio chunk arrives well under a second after connect; that is the Sonic-3 first-byte latency the chapter highlights.
- The greeting sounds conversational, not scripted. The instructions prompt keeps responses short and free of markdown.
- VAD and the underlying turn handling are running for free on CPU; you pay no per-call cost for either.

## Variations

| File | What it does | Book section |
| ---- | ------------ | ------------ |
| `agent.py` | Baseline thirty-line voice agent | Chapter 1, section 4 |

This chapter has no variants. Chapter 2 extends this same skeleton with metrics and a tighter inner loop; later chapters layer tools, handoffs, latency tuning, and deployment on top.

## See also

Chapter 1 of *Voice Agents Handbook* by Mahimai Raja J. ASIN B0FJ7Q96H1.
