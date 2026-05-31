# Chapter 3: Prompts for Voice

Hear the difference between a voice-shaped prompt and a chat-shaped one. Same pipeline, same models, same voice; only the instructions change.

## What this folder contains

- `agent.py`: ACME Plumbing agent loading `prompts/voice.txt` (the seven-rules prompt).
- `agent_chat_shaped.py`: same agent loading `prompts/chat.txt` so you can hear the failure modes.
- `prompts/voice.txt`: terse, no markdown, with explicit "say it" cues. Matches the chapter's upgraded prompt.
- `prompts/chat.txt`: a chat-styled prompt with asterisks, URLs, and hedge stuffing. Reproduces the problems Section 1 of the chapter critiques.

## Setup

Prerequisites: Python 3.11+, uv, accounts with LiveKit, Deepgram, OpenAI, and Cartesia.

```bash
cp .env.example .env
# Fill in keys
uv sync
```

## Run

Run the voice-shaped agent first:

```bash
uv run python agent.py dev
```

Then run the chat-shaped agent and ask it the same questions:

```bash
uv run python agent_chat_shaped.py dev
```

Both files register under the same agent name (`voiceagents-handbook-ch03`), so run one at a time.

## What to listen for

- The chat-shaped agent reads URLs letter by letter ("h-t-t-p-s colon slash slash...") and says "asterisk asterisk" out loud when emphasizing words.
- The chat-shaped agent gives long, well-structured paragraphs you cannot interrupt without feeling rude.
- The voice-shaped agent replies in one or two sentences, prices are spoken as words, and the opening and closing match a phone-call register.

## Variations

| File | What it does | Book section |
| ---- | ------------ | ------------ |
| `agent.py` | Loads the voice-shaped prompt | Section 3 (the upgraded prompt) |
| `agent_chat_shaped.py` | Loads the chat-shaped prompt | Section 1 (a chat prompt, said aloud) |

## See also

Chapter 3 of *Voice Agents Handbook* by Mahimai Raja J. ASIN B0FJ7Q96H1.
