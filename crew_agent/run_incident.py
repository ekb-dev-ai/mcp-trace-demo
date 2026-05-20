"""CrewAI on-call agent — investigates order delays via MCP tools (stdio)."""

import os
import sys
import warnings
from pathlib import Path

from crewai import Agent, Crew, LLM, Process, Task
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters

from otel.setup import configure_telemetry

ROOT = Path(__file__).resolve().parents[1]

os.environ.setdefault("CREWAI_STORAGE_DIR", str(ROOT / ".crewai"))
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
os.environ.setdefault("CREWAI_TESTING", "true")  # skip interactive trace prompt
os.environ.setdefault("LITELLM_LOG", "ERROR")
os.environ.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf")
os.environ.setdefault("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://localhost:4318/v1/traces")
os.environ.setdefault("OTEL_METRICS_EXPORTER", "none")

warnings.filterwarnings("ignore", message="Baggage value for key")


def main() -> None:
    configure_telemetry(service_name="crew-incident-agent", instrument_crewai=True)
    order_id = os.getenv("DEMO_ORDER_ID", "1842")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_server.incident_server"],
        env={**os.environ, "PYTHONPATH": str(ROOT)},
    )

    llm = LLM(
        model=os.getenv("OLLAMA_MODEL", "ollama/llama3.2:latest"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.2,
    )

    print("\n" + "=" * 72)
    print("  MCP-TRACE INCIDENT DEMO")
    print(f"  Order: #{order_id}  |  Jaeger: http://localhost:16686")
    print("=" * 72 + "\n")

    with MCPServerAdapter(server_params, connect_timeout=60) as tools:
        print(f"MCP tools: {[t.name for t in tools]}\n")

        investigator = Agent(
            role="On-Call Incident Investigator",
            goal=(
                "Diagnose why a customer order is delayed using MCP tools only. "
                "Always call get_order first, then check_inventory for the order's SKU."
            ),
            backstory=(
                "You are a calm, precise SRE. You never guess inventory—you call check_inventory. "
                "When inventory is on backorder, you explain the root cause clearly."
            ),
            llm=llm,
            tools=tools,
            verbose=True,
            allow_delegation=False,
            max_iter=15,
        )

        investigation = Task(
            description=(
                f"Order #{order_id} is delayed. The customer wants to know why.\n"
                f"1. Call get_order with order_id={order_id}\n"
                "2. Call check_inventory for the SKU from that order\n"
                "3. If inventory is bad, summarize root cause; only call notify_slack if appropriate\n"
                "You MUST invoke the tools (not just write Action: ... as text). "
                "Return a short incident summary with root cause and ETA if known."
            ),
            expected_output=(
                "A 3-5 sentence incident summary: order status, inventory finding, "
                "root cause, and recommended customer message."
            ),
            agent=investigator,
        )

        crew = Crew(
            agents=[investigator],
            tasks=[investigation],
            process=Process.sequential,
            verbose=True,
            tracing=False,
        )

        result = crew.kickoff()
        print("\n" + "-" * 72)
        print(result)
        print("-" * 72)

    _flush_telemetry()


def _flush_telemetry() -> None:
    try:
        import logfire

        logfire.force_flush()
    except Exception:
        pass


if __name__ == "__main__":
    main()
