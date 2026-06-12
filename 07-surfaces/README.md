# Chapter 7: Surfaces

Three surfaces (phone, browser, mobile), one agent. The transport changes; the agent code does not.

## What this folder contains

- `agent.py`: surface-agnostic baseline. Makes no assumptions about how the participant arrived.
- `phone_agent.py`: SIP-tuned variant. Adds agent-side BVCTelephony noise cancellation (the telephony-tuned model for narrowband SIP audio) and a phone-trained STT model.
- `surface_adaptation.py`: branches on `participant.kind` so SIP callers get narrowband STT plus BVCTelephony and WebRTC clients get the full-bandwidth model. This is the corrected version of the example printed in Chapter 7 section 5.
- `trunk/inbound_trunk.json`: example LiveKit SIP inbound trunk config with Krisp on.
- `trunk/dispatch_rule.json`: example dispatch rule that routes calls into per-call rooms and dispatches this chapter's agent.
- `trunk/README.md`: step-by-step for registering a SIP trunk and pointing your provider at LiveKit.

Browser and mobile clients are not in this Python repo. Start from the official LiveKit starters:

- Browser (Next.js plus LiveKit React): https://github.com/livekit-examples/agent-starter-react
- React Native (iOS and Android): https://github.com/livekit-examples/voice-assistant-react-native
- SwiftUI (iOS): https://github.com/livekit-examples/voice-assistant-swift
- Flutter: https://github.com/livekit-examples/voice-assistant-flutter

## Setup

Prerequisites: Python 3.11+, uv, accounts with LiveKit, Deepgram, OpenAI, and Cartesia. For the phone variant you also need a SIP trunking provider account (Telnyx, Twilio, or Plivo) or a number purchased through LiveKit Phone Numbers.

```bash
cp .env.example .env
# Fill in keys
uv sync
```

## Run

Surface-agnostic baseline:

```bash
uv run python agent.py dev
```

Phone variant (wire up a SIP trunk first; see `trunk/README.md`):

```bash
uv run python phone_agent.py dev
```

Branch-on-surface variant:

```bash
uv run python surface_adaptation.py dev
```

## What to listen for

- Connecting to the same agent from a browser and from a phone call should sound the same. The agent should not mention which surface you are on.
- On phone with BVC enabled, background noise (a TV, a busy street) gets dramatically suppressed before STT sees it. Try calling from a noisy room with `phone_agent.py` and again with plain `agent.py` to hear the difference.
- The phone variant verbally signals when it is doing slow work ("let me check that") and confirms numbers out loud. The browser-grade baseline does not need that nudge as strongly.

## Variations

| File | What it does | Book section |
| ---- | ------------ | ------------ |
| `agent.py` | Surface-agnostic baseline. | Chapter 7 sections 1 and 6 |
| `phone_agent.py` | SIP-tuned: BVCTelephony plus narrowband STT plus phone prompt. | Chapter 7 section 2 |
| `surface_adaptation.py` | Branches on `participant.kind` to pick STT and NC per surface. | Chapter 7 section 5 |
| `trunk/inbound_trunk.json` | SIP inbound trunk with Krisp on. | Chapter 7 section 2 |
| `trunk/dispatch_rule.json` | Dispatch rule mapping numbers to the agent. | Chapter 7 section 2 |

## See also

Chapter 7 of *Voice Agents Handbook* by Mahimai Raja J. ASIN B0FJ7Q96H1.
