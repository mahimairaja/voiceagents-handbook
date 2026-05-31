# SIP trunk configs for Chapter 7

Two JSON files that wire a phone number to the Chapter 7 agent:

- `inbound_trunk.json`: tells LiveKit which phone numbers belong to you and turns on Krisp noise cancellation at the trunk.
- `dispatch_rule.json`: tells LiveKit what to do with calls on those numbers (put them in a new room, dispatch the agent named `voiceagents-handbook-ch07`).

## Prerequisites

You need:

1. A SIP trunking provider account (Telnyx, Twilio, or Plivo) with at least one phone number, OR a number purchased through LiveKit Phone Numbers.
2. The LiveKit CLI installed: `brew install livekit-cli` on macOS, or see https://docs.livekit.io/home/cli/cli-setup/ for other platforms.
3. The CLI authenticated against your LiveKit project: `lk cloud auth`.

## Edit the configs

Before applying, edit `inbound_trunk.json` and replace `+15105550100` with the E.164-formatted phone number you own.

After you create the trunk in the next step, you will receive a trunk ID. Edit `dispatch_rule.json` and replace `<inbound-trunk-id>` with that ID.

## Apply

Create the inbound trunk:

```bash
lk sip inbound create inbound_trunk.json
```

The CLI prints a trunk ID. Copy it into `dispatch_rule.json` where `<inbound-trunk-id>` is.

Create the dispatch rule:

```bash
lk sip dispatch create dispatch_rule.json
```

## Point your SIP provider at LiveKit

Each provider has its own UI for this. The summary: in the provider's dashboard, set the SIP termination URI for your number to LiveKit's SIP endpoint. LiveKit's docs at https://docs.livekit.io/sip/quickstarts/configuring-sip-trunk/ walk through Telnyx, Twilio, and Plivo step by step.

## Test the call

Start the agent worker locally:

```bash
uv run python ../phone_agent.py dev
```

Then call the number from your phone. The dispatch rule routes the inbound SIP call into a new room with prefix `call-`, and LiveKit dispatches the `voiceagents-handbook-ch07` agent into that room. You hear the greeting within a second or two of the call connecting.

## A note on JSON field casing

The wrapper key is snake_case (`trunk`, `dispatch_rule`). The fields inside are camelCase (`krispEnabled`, `trunkIds`, `roomConfig`, `agentName`). The wrapper matches the API method name; the inner fields match the protobuf field names rendered for JSON. This trips up almost every first-time reader. If your CLI rejects the file with an unknown-field error, that is the place to look.

## What to keep in `krispEnabled: true`

Leave it on. Trunk-side Krisp processes the caller's audio before LiveKit hands it to your agent's STT, and the accuracy improvement on real-world phone calls is measurable. Chapter 7 covers the tradeoffs and Appendix A discusses ai-coustics QUAIL as an agent-side complement.
