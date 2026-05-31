# Errata

Corrections to the printed *Voice Agents Handbook* (Mahimai Raja J, June 2026, ASIN B0FJ7Q96H1) that did not make the first edition. Each entry describes the manuscript issue and what this repo does about it.

## 1. Chapter 2 AgentServer paragraph: duplicated clause

The printed text reads:

> The `server` object is your `AgentServer()` with its registered `my_agent` function is what the CLI hands to LiveKit when a job comes in.

The duplicated "is" clause should read:

> The `server` object is the `AgentServer()` with the registered `my_agent` function. This is what the CLI hands to LiveKit when a job comes in.

Repo code at `02-first-agent/agent.py` is correct; only the prose carries the duplicated clause.

## 2. Chapter 5 adaptive-mode summary: run-on sentence

The printed text contains a run-on that drops a clause boundary around the adaptive interruption summary. The repo's `05-latency-turn-taking/adaptive_interruption.py` and its README clarify the prerequisites (LiveKit Cloud, VAD, aligned-transcript STT, and a non-realtime LLM) and the silent fallback to VAD-only mode.

## 3. Chapter 7 §5 surface-adaptation example: tautological branch

The printed example sets `stt_model = "deepgram/nova-3"` in both the SIP and non-SIP branches, making the branch tautological while the surrounding prose promises a phone-tuned variant. The repo's `07-surfaces/surface_adaptation.py` is the corrected version: the SIP branch uses a phone-tuned STT alternative, the WebRTC branch uses the default browser-grade STT.

## 4. Conclusion CTA: stray spaces around "Voice AI Community"

The Conclusion's closing call-to-action contains stray internal spaces in:

> The Voice AI Community ( Open Source ) on LinkedIn

It should read:

> The Voice AI Community (Open Source) on LinkedIn

No repo code change required.

## 5. Cartesia voice ID without discovery note

The Cartesia voice ID `9626c31c-bec5-4cca-baa8-f8ba9e84c8bc` (Jacqueline) appears in Chapters 1, 2, and 4 without an explanation of how to discover or copy a different voice ID. The repo's `02-first-agent/README.md` adds a one-line note: you can browse other voices at play.cartesia.ai and copy the ID from the URL.
