#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}━━━ mcp-trace-demo ━━━${NC}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# --- Jaeger ---
if ! curl -sf http://localhost:16686 >/dev/null 2>&1; then
  echo -e "${CYAN}Starting Jaeger (docker compose)...${NC}"
  docker compose up -d
  echo "Waiting for Jaeger UI..."
  for _ in {1..30}; do
    curl -sf http://localhost:16686 >/dev/null 2>&1 && break
    sleep 1
  done
fi
echo -e "${GREEN}✓ Jaeger UI: http://localhost:16686${NC}"

# --- Ollama ---
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
if ! curl -sf "${OLLAMA_BASE_URL}/api/tags" >/dev/null 2>&1; then
  echo -e "${RED}✗ Ollama not reachable at ${OLLAMA_BASE_URL}${NC}"
  echo "  Install: https://ollama.com  then: ollama serve"
  exit 1
fi
MODEL="${OLLAMA_MODEL:-ollama/llama3.2}"
TAG="${MODEL#ollama/}"
if ! curl -sf "${OLLAMA_BASE_URL}/api/tags" | grep -q "\"${TAG%%:*}\""; then
  echo -e "${CYAN}Pulling model ${TAG}...${NC}"
  ollama pull "${TAG}"
fi
echo -e "${GREEN}✓ Ollama ready (${MODEL})${NC}"

# --- Python env (Poetry in-project .venv) ---
if [[ ! -d .venv ]]; then
  echo -e "${CYAN}Creating venv and installing deps (poetry)...${NC}"
  poetry install --no-interaction --quiet
else
  poetry install --no-interaction --quiet 2>/dev/null || true
fi
# shellcheck disable=SC1091
source .venv/bin/activate

export PYTHONPATH="$ROOT"
export CREWAI_STORAGE_DIR="${CREWAI_STORAGE_DIR:-$ROOT/.crewai}"
export CREWAI_TRACING_ENABLED=false
export OLLAMA_MODEL="${OLLAMA_MODEL:-ollama/llama3.2:latest}"
export OTEL_EXPORTER_OTLP_PROTOCOL="${OTEL_EXPORTER_OTLP_PROTOCOL:-http/protobuf}"
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="${OTEL_EXPORTER_OTLP_TRACES_ENDPOINT:-http://localhost:4318/v1/traces}"
export DEMO_ORDER_ID="${DEMO_ORDER_ID:-1842}"

echo -e "${CYAN}Running incident crew (order #${DEMO_ORDER_ID})...${NC}\n"
python -m crew_agent.run_incident </dev/null

echo -e "\n${GREEN}━━━ Next: open Jaeger ━━━${NC}"
echo "  1. http://localhost:16686"
echo "  2. Search → Service: crew-incident-agent"
echo "  3. Find trace with MCP send/handle tools/call check_inventory"
echo "  4. Compare trace_id with service mcp-incident-server (same trace, SEP-414)"
