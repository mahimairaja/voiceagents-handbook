# Chapter 2: Your First Agent

Clone-to-running in twenty minutes. Speak, hear, change one line, listen again.

## What this folder contains

- `agent.py`: the 40-line working agent the chapter walks through. Same provider stack as Chapter 1, with the system prompt tuned for the ear.
- `agent_with_metrics.py`: the same agent with a `metrics_collected` listener that prints LLM TTFT and TTS time-to-first-audio per turn so you can run the inner loop with numbers in your terminal.

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

For the metrics variant:

```bash
uv run python agent_with_metrics.py dev
```

## What to listen for

- The agent greets you first (the `generate_reply` call at the bottom of the entrypoint).
- Speak. The transcription appears in the terminal as Deepgram finalizes it; the agent's reply streams back in audio.
- Change the `instructions` string in `agent.py` (give it a different personality), save, and run again. This is the inner loop the chapter teaches: change one thing, listen again.

## Picking a different voice

The default voice ID `9626c31c-bec5-4cca-baa8-f8ba9e84c8bc` is Cartesia's Jacqueline. Browse the voice library at play.cartesia.ai and copy the ID from the URL of any voice you like.

## Variations

| File | What it does | Book section |
| ---- | ------------ | ------------ |
| `agent.py` | Hero agent: VAD, Deepgram STT, OpenAI LLM, Cartesia TTS. | Chapter 2 sections 2 and 3 |
| `agent_with_metrics.py` | Adds a `metrics_collected` listener and prints per-turn TTFT and time-to-first-audio. | Chapter 2 inner-loop discussion |

## See also

Chapter 2 of *Voice Agents Handbook* by Mahimai Raja J. ASIN B0FJ7Q96H1.
