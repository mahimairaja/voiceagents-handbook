#!/usr/bin/env bash
# Graceful drain script for a self-hosted voice agent.
#
# Voice agents serve sessions that can last forty minutes. A web-style
# SIGKILL-after-30-seconds is the wrong default: it cuts callers off
# mid-sentence. This script mirrors what LiveKit Cloud does on a rolling
# deploy (give existing instances up to an hour to drain), but for a process
# you run yourself behind systemd, Kubernetes, or docker compose.
#
# Usage:
#   ./drain.sh <pid>
#
# Environment:
#   LIVEKIT_DRAIN_TIMEOUT - seconds to wait between SIGTERM and SIGKILL.
#                           Defaults to 600 (ten minutes). Set higher if your
#                           call patterns routinely exceed ten minutes.

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "usage: $0 <pid>" >&2
    exit 2
fi

PID=$1
TIMEOUT=${LIVEKIT_DRAIN_TIMEOUT:-600}

if ! kill -0 "$PID" 2>/dev/null; then
    echo "drain.sh: no process with pid $PID" >&2
    exit 1
fi

echo "drain.sh: sending SIGTERM to pid $PID; waiting up to ${TIMEOUT}s for in-flight sessions to finish."
kill -TERM "$PID"

ELAPSED=0
while kill -0 "$PID" 2>/dev/null; do
    if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
        echo "drain.sh: timeout reached after ${TIMEOUT}s; sending SIGKILL to pid $PID." >&2
        kill -KILL "$PID" 2>/dev/null || true
        exit 1
    fi
    sleep 5
    ELAPSED=$((ELAPSED + 5))
    if [ $((ELAPSED % 60)) -eq 0 ]; then
        echo "drain.sh: still draining (${ELAPSED}s / ${TIMEOUT}s)..."
    fi
done

echo "drain.sh: pid $PID exited cleanly after ${ELAPSED}s."
