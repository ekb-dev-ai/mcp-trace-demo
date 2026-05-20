# mcp-trace-demo

**MCP + CrewAI + Ollama + OpenTelemetry** — incident demo with distributed tracing across stdio.

Every MCP `tools/call` is traced from the CrewAI agent process through the MCP server subprocess (W3C trace context in `params._meta`, [SEP-414](https://modelcontextprotocol.io/seps/414-request-meta)). Visualize in **Jaeger**.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (for Jaeger)
- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation)
- [Ollama](https://ollama.com) (for the full demo only)

## Quick start

```bash
# 1. Clone and enter the repo
git clone git@github-youtube:ekb-dev-ai/mcp-trace-demo.git
cd mcp-trace-demo

# 2. Config (optional — defaults work for local Jaeger + Ollama)
cp .env.example .env

# 3. Start Jaeger
docker compose up -d

# 4. Pull the LLM (first run only)
ollama pull llama3.2:latest

# 5. Install Python deps
poetry install

# 6. Run the one-command demo
chmod +x scripts/*.sh
./scripts/demo.sh
```

Then open **http://localhost:16686** → service `crew-incident-agent` → open a trace. You should see the same `trace_id` on client and server MCP spans (stdio, SEP-414).

## Scripts

| Script | What it does |
|--------|----------------|
| `./scripts/demo.sh` | Full demo: Jaeger + Ollama + CrewAI incident crew (order #1842) |
| `./scripts/quick_trace_demo.sh` | Fast path (~5s): MCP + Jaeger only, no Ollama |
| `./scripts/verify_setup.sh` | Import check (no LLM, no Docker) |
| `./scripts/jaeger_find_trace.sh [service]` | Print latest trace spans from Jaeger API |

## No Ollama?

Trace-only rehearsal:

```bash
docker compose up -d
poetry install
./scripts/quick_trace_demo.sh
```

## Manual run

```bash
poetry install
source .venv/bin/activate
export PYTHONPATH="$(pwd)"
export CREWAI_STORAGE_DIR="$(pwd)/.crewai"
export CREWAI_TRACING_ENABLED=false
python -m crew_agent.run_incident
```

MCP server (stdio, usually spawned by the agent):

```bash
PYTHONPATH="$(pwd)" python -m mcp_server.incident_server
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `ollama/llama3.2:latest` | CrewAI LLM |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API |
| `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` | `http://localhost:4318/v1/traces` | Jaeger OTLP HTTP |
| `DEMO_ORDER_ID` | `1842` | Order to investigate |
| `INCIDENT_SLOW_SECONDS` | `2.5` | Inventory latency |
| `LOGFIRE_TOKEN` | — | Optional Logfire export |

## Project layout

```
mcp_server/incident_server.py   # FastMCP server (stdio)
crew_agent/run_incident.py      # CrewAI on-call agent
otel/setup.py                   # logfire.instrument_mcp() + CrewAI OTel
scripts/demo.sh                 # One-command demo
docker-compose.yml              # Jaeger all-in-one
```

## References

- [SEP-414: Trace context in `_meta`](https://modelcontextprotocol.io/seps/414-request-meta)
- [OpenTelemetry MCP semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/mcp/)

## License

MIT
