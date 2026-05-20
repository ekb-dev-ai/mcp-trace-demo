#!/usr/bin/env bash
# Quick health check: MCP server module imports (no Ollama).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate
python -c "import mcp_server.incident_server; import crew_agent.run_incident; print('OK: imports')"
