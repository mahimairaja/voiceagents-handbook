# Chapter 8: Testing with Synthetic Callers

A small ACME Plumbing agent plus a pytest suite that drives it through text-mode conversations and evaluates the results with LLM judges.

## What this folder contains

- `agent.py`: an ACME Plumbing receptionist with two function tools (`get_service_price`, `book_appointment`). Same `AgentServer` shape as every other chapter; runs with `uv run python agent.py dev` for live calls.
- `tests/conftest.py`: pytest fixtures: `judge_llm`, `agent_session`, `simulated_user`.
- `tests/test_greeting.py`: single-turn tests that judge the assistant's greeting and its handling of "where can I find this online" (no URL spell-out).
- `tests/test_booking_flow.py`: multi-turn tests covering the happy path (price quote, booking confirmation) and one failure path (slot unavailable, mocked with `mock_tools`).
- `tests/test_judges.py`: conversation-level tests using `JudgeGroup` with the built-in judges (`task_completion_judge`, `accuracy_judge`, `tool_use_judge`, `relevancy_judge`, `safety_judge`).

## Setup

Prerequisites: Python 3.11+, uv, accounts with LiveKit Cloud, Deepgram, OpenAI, and Cartesia. The pytest suite only needs the OpenAI key (judges and inference LLM both run through OpenAI); the LiveKit and provider keys are only needed if you also want to talk to the agent live with `uv run python agent.py dev`.

```bash
cp .env.example .env
# Fill in keys (OPENAI_API_KEY is the only one the tests need)
uv sync
```

## Run

The tests:

```bash
uv run pytest
```

The live agent (optional):

```bash
uv run python agent.py dev
```

## What to listen for

- The tests are fast and cheap because no STT or TTS runs. The synthetic caller is a string; the agent's response is text; the judge is a second LLM call. Every test in this folder finishes in seconds.
- Judge verdicts are not deterministic at the edges. If a test flakes, the right fix is usually a looser `intent` string, not a retry loop. The chapter discusses this at length.
- `JudgeGroup` is the test you keep running on every deploy. Five behavioral guarantees per commit: task completed, responses grounded, tools used correctly, on topic, nothing unsafe said.

## Variations

| File | What it does | Book section |
| ---- | ------------ | ------------ |
| `agent.py` | The agent under test. Greeting plus two function tools. | Section 3 (test setup) |
| `tests/conftest.py` | Shared fixtures: judge LLM, agent session, simulated user. | Section 3 |
| `tests/test_greeting.py` | Single-turn judge tests. | Section 4 (the three things you test) |
| `tests/test_booking_flow.py` | Multi-turn flow, tool-call assertion, and a `mock_tools` failure path. | Sections 4, 6 (mocking tools) |
| `tests/test_judges.py` | `JudgeGroup` across a full intake conversation. | Section 5 (the LLM judge) |

## See also

Chapter 8 of *Voice Agents Handbook* by Mahimai Raja J. ASIN B0FJ7Q96H1.
