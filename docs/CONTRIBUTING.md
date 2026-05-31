# Contributing

This repo is the code companion to *Voice Agents Handbook* by Mahimai Raja J (June 2026, ASIN B0FJ7Q96H1). It tracks current `livekit-agents` releases on `main`. The print edition's frozen state lives at the `book-v1` tag.

## Filing issues

Three templates. Pick the one that fits.

### Book errata

A prose mistake in the printed book: a missing word, a duplicated clause, a stale reference, a typo. Corrections land in `docs/ERRATA.md`. Use the **Book errata** template.

### Repo bug

Code in this repo that does not run or does not behave as documented. Include the chapter folder, the exact command you ran, and the output. Use the **Repo bug** template.

### Provider drift

A provider's API changed and broke an example. Include the provider, the breaking change, and a link to the provider's release notes. Use the **Provider drift** template.

## Pull requests

Small typo fixes can go straight to a PR. For anything larger, open an issue first.

## Tag policy

- `book-v1`: frozen at the June 2026 print launch. Check this tag out if you want the print-edition code.
- `main`: evolves with new `livekit-agents` releases. Subsequent tags (`book-v1.1`, `book-v2`, ...) document changes since print in release notes.

## Style

- Python 3.11+
- `uv`, not `pip`
- `ruff` for lint and format (line length 100; the root `pyproject.toml` holds the config)
- No em-dashes anywhere in prose, code comments, or commit messages
- Real provider names, not placeholders
- Working code in every fenced block; no pseudocode

## Local checks before pushing

```bash
uvx ruff check .
uvx ruff format --check .
python tools/check_env_examples.py
```

CI runs the same checks plus a per-chapter `uv sync` and `python -m py_compile` matrix.
