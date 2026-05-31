# Chapter 5: Latency, Interruptions, and Turn-Taking

Three timing failure modes (the pause, the false interruption, the hesitation gap) and the three levers in `TurnHandlingOptions` that fix them.

## What this folder contains

- `agent.py`: tuned baseline. Adaptive interruption on, endpointing at the conservative 0.5 / 3.0 window, preemptive generation on (default) with preemptive TTS off. Matches section 6 of the chapter.
- `preemptive_generation.py`: preemptive generation plus preemptive TTS. Demonstrates the perceived-latency win and the footgun (slow LLMs make it a no-op).
- `adaptive_interruption.py`: adaptive interruption mode in isolation. Shows the four prerequisites (LiveKit Cloud, VAD, non-realtime LLM, aligned-transcript STT) and the silent VAD-only fallback when any of them fail.
- `manual_turn_tuning.py`: VAD-only baseline with explicit endpointing thresholds. The "if you can't run adaptive" configuration.
- `pyproject.toml`: pins `livekit-agents==1.5.15`, plus `livekit-plugins-turn-detector` for the multilingual model.
- `.env.example`: provider keys.

## Setup

Prerequisites: Python 3.11+, uv, accounts with LiveKit, Deepgram, OpenAI, Cartesia.

```bash
cp .env.example .env
# Fill in keys
uv sync
```

## Run

```bash
uv run python agent.py dev
```

Each variant is independently runnable:

```bash
uv run python preemptive_generation.py dev
uv run python adaptive_interruption.py dev
uv run python manual_turn_tuning.py dev
```

## What to listen for

- **agent.py**: cadence should feel natural. Backchannels like "mm-hmm" should not stop the agent.
- **preemptive_generation.py**: first audio should arrive sooner after you stop talking. The win is in the first 200-300 ms.
- **adaptive_interruption.py**: ask the agent to explain something, then say "mm-hmm" and "okay" while it talks. It should keep going. Then say "wait, hold on" and it should stop.
- **manual_turn_tuning.py**: the contrast file. Acknowledgments may cut the agent off. The pause feels tighter on quick exchanges, sloppier on hesitant ones.

Run each on a real phone if you can. The terminal will mislead you about cadence.

## Variations

| File | What it does | Book section |
| ---- | ------------ | ------------ |
| `agent.py` | Tuned baseline with adaptive interruption | Section 6 |
| `preemptive_generation.py` | Preemptive LLM and TTS, with the slow-model footgun called out | Section 4 |
| `adaptive_interruption.py` | Adaptive mode in isolation, with the four prerequisites | Section 5 |
| `manual_turn_tuning.py` | VAD-only with explicit endpointing thresholds | Section 3 |

## See also

Chapter 5 of *Voice Agents Handbook* by Mahimai Raja J. ASIN B0FJ7Q96H1.
