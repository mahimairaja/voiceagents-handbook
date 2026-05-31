# Chapter 6: Common Patterns

Six architectural shapes voice agents take in production, one runnable file per pattern.

## What this folder contains

- `agent.py`: triage agent that routes callers to a billing, dispatch, or emergency specialist (Pattern 3, the hero file).
- `tool_router.py`: conversational agent with multiple function tools (Pattern 1).
- `survey_agent.py`: intake agent with a `TaskGroup` that completes once required fields are collected (Pattern 2).
- `parallel_subagent.py`: observer agent that watches the conversation and emits side-channel alerts without ever speaking (Pattern 4).
- `script_agent.py`: consent disclosure that reads uninterruptibly, then hands off to a conversational agent (Pattern 5).
- `outbound_caller.py`: outbound dialer that creates a SIP participant, waits for the callee to speak first, then runs the conversation (Pattern 6).

## Setup

Prerequisites: Python 3.11+, uv, accounts with LiveKit, Deepgram, OpenAI, Cartesia. Anthropic and Google are listed in `.env.example` for readers swapping the triage LLM. `SIP_OUTBOUND_TRUNK_ID` is only needed if you run `outbound_caller.py`.

```bash
cp .env.example .env
# Fill in keys
uv sync
```

## Run

```bash
uv run python agent.py dev
```

To run a different pattern:

```bash
uv run python tool_router.py dev
uv run python survey_agent.py dev
uv run python parallel_subagent.py dev
uv run python script_agent.py dev
```

To run the outbound caller, set `SIP_OUTBOUND_TRUNK_ID` and dispatch with the LiveKit CLI:

```bash
uv run python outbound_caller.py dev
lk dispatch create \
    --agent-name voiceagents-handbook-ch06 \
    --room outbound-test \
    --metadata '{"phone_number": "+15551234567"}'
```

## What to listen for

- `agent.py`: the triage agent should hand off within two or three turns. Listen for the moment the voice character changes when a specialist takes over.
- `script_agent.py`: try speaking over the consent disclosure. The agent will not stop. Once the disclosure ends, the conversational agent should acknowledge what you said by content.
- `outbound_caller.py`: the agent must not speak first. The callee's "hello" is the cue.

## Variations

| File | What it does | Book section |
| ---- | ------------ | ------------ |
| `agent.py` | Triage agent routing to three specialists | 6.3 The triage agent |
| `tool_router.py` | Conversational agent with multiple function tools | 6.1 The conversational agent |
| `survey_agent.py` | `AgentTask` that completes once required fields are filled | 6.2 The survey agent |
| `parallel_subagent.py` | Observer that scores transcripts against a rubric on a side channel | 6.4 The observer agent |
| `script_agent.py` | Uninterruptible disclosure followed by `update_agent` handoff | 6.5 The script agent |
| `outbound_caller.py` | SIP outbound dialer that waits for the callee to speak | 6.6 The outbound agent |

## See also

Chapter 6 of *Voice Agents Handbook* by Mahimai Raja J. ASIN B0FJ7Q96H1.
