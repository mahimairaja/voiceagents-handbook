# Production-shaped image for a Chapter 9 voice agent.
#
# This is the illustrative version from the book: pinned base, lockfile-driven
# install, non-root user, VAD weights baked in. The official template from
# `lk agent create` is more sophisticated (multi-stage build, harder .dockerignore);
# use that for real deployments. This one exists so the chapter compiles end to end.

FROM python:3.11-slim

# Build dependencies for native packages (silero ONNX runtime, audio codecs).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        ffmpeg \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv into a system location so the non-root runtime user can use it
# without copying or symlinking from /root/.local.
ENV UV_INSTALL_DIR=/usr/local/bin
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Create the non-root runtime user before any sync so the dependency venv and
# model caches land in the user's home directory and are owned by it.
RUN useradd --create-home --shell /bin/bash agent
WORKDIR /app
RUN chown agent:agent /app

USER agent

# Cache layer: install dependencies from the lockfile before copying source.
# No `|| uv sync` fallback: if the lockfile is out of date, fail the build
# rather than silently regenerate and produce a non-reproducible image.
ENV UV_COMPILE_BYTECODE=1
COPY --chown=agent:agent pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

# Application code last so source edits do not bust the dependency layer.
COPY --chown=agent:agent agent.py prewarm.py observability.py ./

# Pre-download silero VAD weights into the agent user's cache so the first
# session does not pay for a model download on cold start. The multilingual
# turn detector loads its weights on first use; if cold-start latency for that
# is a problem in your environment, extend this line to bake those in too.
RUN uv run python -c "from livekit.plugins import silero; silero.VAD.load()"

# Health check port. The agent server binds 8081 by default.
EXPOSE 8081

# `start` is the production command. `dev` auto-reloads and should not ship.
CMD ["uv", "run", "python", "agent.py", "start"]
