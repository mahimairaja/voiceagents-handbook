# Chapter 4: Function Tools, State, and Handoffs

The ACME Plumbing booking flow: function tools, typed `userdata`, and a handoff to a billing specialist.

## What this folder contains

- `agent.py`: ACME Plumbing booking hero. Reception agent with pricing lookup, booking tool, typed `CallData` userdata, and a handoff to `BillingAgent`.
- `function_tool_basic.py`: minimal single-tool example. The decorator, the docstring-as-prompt, the return shape.
- `typed_userdata.py`: typed `userdata` as the per-session spine. Two tools writing to and reading from a `CallData` dataclass.
- `handoff_pattern.py`: two `Agent` subclasses, one tool that returns the new agent, `chat_ctx.copy(exclude_instructions=True)` to carry the conversation forward.
- `error_path.py`: a tool that fails on purpose. Shows `context.disallow_interruptions()` and `ToolError` with LLM-readable recovery instructions.

## Setup

Prerequisites: Python 3.11+, uv, accounts with LiveKit, Deepgram, OpenAI, and Cartesia. Anthropic is optional (only if you swap to Claude Haiku).

```bash
cp .env.example .env
# Fill in keys
uv sync
```

## Run

```bash
uv run python agent.py dev
```

Each variant file is independently runnable:

```bash
uv run python function_tool_basic.py dev
uv run python typed_userdata.py dev
uv run python handoff_pattern.py dev
uv run python error_path.py dev
```

## What to listen for

- The pause when a tool fires. Ask *"how much for a drain cleaning?"* and listen for the brief beat while the LLM decides to call `get_service_price`, the tool runs, and the LLM composes its reply.
- State surviving the handoff. Tell the reception agent your name, then ask to be transferred to billing. The billing agent should know your name without asking again.
- Error recovery as speech. In `error_path.py`, request a booking and the tool will raise `BookingAPIDown`. Listen for the agent reading the `ToolError` instruction back as a natural offer to take your number.

## Variations

| File | What it does | Book section |
| ---- | ------------ | ------------ |
| `agent.py` | Full ACME Plumbing booking flow: pricing tool, booking tool, typed userdata, handoff to billing. | 4.1 through 4.5 |
| `function_tool_basic.py` | One read-only tool, no state, no handoff. | 4.1 A first tool |
| `typed_userdata.py` | Two tools sharing a `CallData` dataclass across turns. | 4.3 State across tools |
| `handoff_pattern.py` | Reception agent transfers to billing agent mid-call. | 4.4 When one agent is not enough |
| `error_path.py` | `disallow_interruptions()` plus `ToolError` for a mutating tool that fails. | 4.2 Mutating tools |

## Haiku for tool-heavy work (Appendix A callout)

When an agent's primary job is to drive a sequence of function-tool calls (rather than long-form reasoning), Claude Haiku 4.5 often pays for itself in latency. The pricing and booking flow in `agent.py` is a candidate. To try it, install `livekit-plugins-anthropic` (already pinned in `pyproject.toml`), set `ANTHROPIC_API_KEY`, and swap the LLM line:

```python
from livekit.plugins import anthropic
# ...
llm=anthropic.LLM(model="claude-haiku-4-5"),
```

Listen for the difference in turn-to-tool latency, not in voice quality. The chapter and Appendix A both note that tool-heavy agents see the biggest wins from a fast model on the decision step.

## See also

Chapter 4 of *Voice Agents Handbook* by Mahimai Raja J. ASIN B0FJ7Q96H1.
