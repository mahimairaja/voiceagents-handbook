#!/usr/bin/env python3
"""Validate that every chapter folder has a sane .env.example.

CI helper. Fails if:

- a NN-* chapter folder is missing .env.example
- any .env.example contains values that look like real secret keys

Run from the repo root::

    python tools/check_env_examples.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Real-looking secret prefixes. A committed value that starts with one of
# these implies a live API key slipped into the committed .env.example
# instead of being filled in by the reader.
SECRET_PATTERNS = [
    re.compile(r"=\s*sk-[a-zA-Z0-9_-]{20,}"),
    re.compile(r"=\s*dg_[a-zA-Z0-9_-]{20,}"),
    re.compile(r"=\s*lk_[a-zA-Z0-9_-]{20,}"),
    re.compile(r"=\s*sk_live_[a-zA-Z0-9_-]{20,}"),
    re.compile(r"=\s*[a-f0-9]{40,}"),
]


def main() -> int:
    failures: list[str] = []
    chapter_dirs = sorted(
        p for p in REPO_ROOT.iterdir() if p.is_dir() and re.match(r"^\d{2}-", p.name)
    )

    if not chapter_dirs:
        print("no NN-* chapter folders found at repo root", file=sys.stderr)
        return 1

    for chapter in chapter_dirs:
        env_example = chapter / ".env.example"
        if not env_example.is_file():
            failures.append(f"{chapter.name}: missing .env.example")
            continue

        content = env_example.read_text(encoding="utf-8")
        for pattern in SECRET_PATTERNS:
            if pattern.search(content):
                # Report only the file and the pattern label, never the
                # matched content. We do not want CI logs to echo secrets.
                failures.append(
                    f"{chapter.name}/.env.example: value matches secret-like pattern /{pattern.pattern}/"
                )

    if failures:
        print("env-example validation failed:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print(f"OK: {len(chapter_dirs)} chapters validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
