#!/usr/bin/env bash
# Fast demo without Ollama — MCP + Jaeger only (~5s).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ ! -d .venv ]]; then
  poetry install --no-interaction --quiet
fi
# shellcheck disable=SC1091
source .venv/bin/activate
export PYTHONPATH="$ROOT" OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://localhost:4318/v1/traces OTEL_METRICS_EXPORTER=none
docker compose up -d 2>/dev/null || true
python scripts/trace_smoke_test.py
sleep 2
chmod +x scripts/jaeger_find_trace.sh
./scripts/jaeger_find_trace.sh trace-smoke-test
