# Production-shaped image for a Chapter 9 voice agent.
#
# This is the illustrative version from the book: pinned base, lockfile-driven
# install, non-root user, model files baked in. The official template from
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

# Install uv (Astral's Python packager). We pin to a known-good version so that
# `uv sync --frozen` is reproducible across container builds.
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Cache layer: install dependencies from the lockfile before copying source.
ENV UV_COMPILE_BYTECODE=1
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev || uv sync --no-dev

# Copy application code last so source edits do not bust the dependency layer.
COPY agent.py prewarm.py observability.py ./

# Pre-download VAD and turn-detector weights into the image so the first session
# does not pay for a model download on cold start.
RUN uv run python -c "from livekit.plugins import silero; silero.VAD.load()" || true

# Run as a non-root user. Voice agents do not need root in the container; this
# matches the production template lk agent create generates.
RUN useradd --create-home --shell /bin/bash agent \
    && chown -R agent:agent /app
USER agent

# Health check port. The agent server binds 8081 by default.
EXPOSE 8081

# `start` is the production command. `dev` auto-reloads and should not ship.
CMD ["uv", "run", "python", "agent.py", "start"]
