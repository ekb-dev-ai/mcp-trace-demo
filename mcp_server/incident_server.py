from __future__ import annotations

import logfire
import time
from typing import Any
from otel.setup import configure_telemetry
from mcp.server.fastmcp import FastMCP

configure_telemetry(service_name="mcp_incident_server", stdio_safe=True)


app = FastMCP(
    "incident_ops",
    instructions=(
        "E-commerce incident tools. Use get_order first, then check_inventory for the SKU," \
        "then notify_slack for alerting"
    )
)

# Fake data
ORDERS: dict[str, dict[str, Any]] = {
    "1842": {
        "order_id": "1842",
        "customer": "Alex Rivera",
        "sku" : "SKU_DELAYED_42",
        "product": "Wirless Earbuds",
        "status": "processing",
        "warehouse": "us-east-1"
    },
    "9999": {
        "order_id": "9999",
        "customer": "Demo User",
        "sku" : "SKU_OK_01",
        "product": "Wirless Earbuds",
        "status": "shipped",
        "warehouse": "us-east-1"
    },

}

INVENTORY: dict[str, dict[str, Any]] = {
    "SKU_OK_01": {
        "sku": "SKU_OK_01",
        "available": 420,
        "reserved": 12,
        "status": "healthy"
    },
    "SKU_DELAYED_42": {
        "sku": "SKU_DELAYED_42",
        "available": 0,
        "reserved": 89,
        "status": "backorder",
        "eta_days": 14
    }
}

FAIL_SKU = "SKU_DELAYED_42"
SLOW_SECONDS = 20


@app.tool()
def get_order(order_id: str) -> dict[str, Any]:
    """ Look up an order by ID (e.g. 1842)"""
    with logfire.span("get_order", order_id=order_id):
        order = ORDERS.get(order_id.strip())
        if order is None:
            return {
                "found": False,
                "order_id": order_id,
                "message": f"No order found with id {order_id}"
            }
        logfire.info("order loaded", order=order)
        return {"found": True, **order}

@app.tool()
def check_inventory(sku: str) -> dict[str, Any]:
    """Check warehouse stock for a SKU. Maybe slow under load"""
    sku = sku.strip()
    if "DELAYED" in sku.upper():
        sku = FAIL_SKU
    
    with logfire.span("check_inventory", sku=sku, slow_seconds = SLOW_SECONDS):
        logfire.info("inventory lookup started", sku=sku)
        time.sleep(SLOW_SECONDS)
        record = INVENTORY.get(sku)
        if record is None:
            return {
                "found": False,
                "sku": sku,
                "message": f"Unknown sku {sku}"
            }
        
        if sku == FAIL_SKU:
            logfire.error("inventory backorder blocks fulfillment", sku=sku, record=record)
            return {
                "found": False,
                "sku": sku,
                "isError": True,
                "status": "backorder",
                "available": record["available"],
                "eta_days": record.get("eta_days", "?"),
                "reserved": record["reserved"],
                "message": (
                        f"SKU {sku} is on backorder ({record['reserved']} units reserved,"
                        f"0 available). Estimated restock: {record.get('eta_days', '?')}"
                    )
            }
        logfire.info("inventory healthy", sku=sku, available=record["available"])
        return {"found": True, "isError": False, **record}

@app.tool()
def notify_slack(channel:str, message: str) -> dict[str, Any]:
    """ Post incident update to a Slack channel"""
    with logfire.span("notify_slack", channel=channel):
        logfire.info("slack notification sent", channel=channel, message=message)
        return {
            "status": "sent",
            "channel": channel,
            "message": message
        }

def main() -> None:
    app.run(transport="stdio")


if __name__ == "__main__":
    main()