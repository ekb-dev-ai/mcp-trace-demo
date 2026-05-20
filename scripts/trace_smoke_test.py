#!/usr/bin/env python3
"""
Smoke test: MCP client calls incident server over stdio, exports spans to Jaeger.
Does not need Ollama. Run: python scripts/trace_smoke_test.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from otel.setup import configure_telemetry


async def main() -> None:
    configure_telemetry(service_name="trace-smoke-test")
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_server.incident_server"],
        env={**os.environ, "PYTHONPATH": str(ROOT)},
    )

    print("Calling get_order + check_inventory over stdio (traced)...")
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            order = await session.call_tool("get_order", {"order_id": "1842"})
            print("get_order:", order.content)
            inv = await session.call_tool(
                "check_inventory", {"sku": "SKU-DELAYED-42"}
            )
            print("check_inventory:", inv.content)

    print("\nDone. Check Jaeger: http://localhost:16686")
    print("Service: trace-smoke-test | mcp-incident-server")


if __name__ == "__main__":
    asyncio.run(main())
