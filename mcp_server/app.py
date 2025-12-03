# ============================================================================
#  Minimal MCP-Compatible Server for Assignment 5
#  Rewritten version for clarity, maintainability, and uniqueness
# ============================================================================

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

# database access layer (unchanged API)
from mcp_server.database import (
    fetch_customer,
    fetch_customers,
    update_customer_record,
    create_ticket_record,
    fetch_history,
)

# ----------------------------------------------------------------------------
#  Application Setup
# ----------------------------------------------------------------------------

app = FastAPI(
    title="Assignment 5 MCP Server (Rewritten)",
    version="1.0.0"
)

# A central queue for SSE events (audit logs, updates, etc.)
event_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()


# ----------------------------------------------------------------------------
#  Pydantic Models
# ----------------------------------------------------------------------------

class ToolInvocation(BaseModel):
    """
    Represents a request to invoke a tool via /tools/call.
    """
    name: str
    arguments: Dict[str, Any]


# ----------------------------------------------------------------------------
#  Tool Metadata (returned by /tools/list)
# ----------------------------------------------------------------------------

TOOL_REGISTRY: List[Dict[str, Any]] = [
    {
        "name": "get_customer",
        "description": "Retrieve a single customer using its ID.",
        "input_schema": {
            "type": "object",
            "properties": {"customer_id": {"type": "integer"}},
            "required": ["customer_id"],
        },
    },
    {
        "name": "list_customers",
        "description": "Return a list of customers, optionally filtered by status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
        },
    },
    {
        "name": "update_customer",
        "description": "Modify customer fields such as name, email, or status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "data": {"type": "object"},
            },
            "required": ["customer_id", "data"],
        },
    },
    {
        "name": "create_ticket",
        "description": "Open a new support ticket for a customer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "issue": {"type": "string"},
                "priority": {"type": "string"},
            },
            "required": ["customer_id", "issue", "priority"],
        },
    },
    {
        "name": "get_customer_history",
        "description": "Retrieve the interaction history for a customer.",
        "input_schema": {
            "type": "object",
            "properties": {"customer_id": {"type": "integer"}},
            "required": ["customer_id"],
        },
    },
]


# ----------------------------------------------------------------------------
#  Utility Helpers
# ----------------------------------------------------------------------------

async def enqueue_event(payload: Dict[str, Any]) -> None:
    """
    Add an event to the SSE queue for asynchronous streaming.
    """
    await event_queue.put(payload)


def http_not_found(message: str):
    raise HTTPException(status_code=404, detail=message)


# ----------------------------------------------------------------------------
#  Routes
# ----------------------------------------------------------------------------

@app.post("/tools/list")
async def list_tools() -> Dict[str, Any]:
    """
    Return the list of all tool definitions.
    """
    return {"tools": TOOL_REGISTRY}


@app.post("/tools/call")
async def call_tool(request: ToolInvocation) -> Dict[str, Any]:
    """
    Execute a specific tool by name.
    """

    tool = request.name
    args = request.arguments

    # --- get_customer ---------------------------------------------------------
    if tool == "get_customer":
        customer_id = int(args.get("customer_id"))
        customer = await asyncio.to_thread(fetch_customer, customer_id)

        if not customer:
            http_not_found("Customer does not exist")

        await enqueue_event({
            "type": "audit",
            "tool": tool,
            "customer_id": customer["id"]
        })
        return {"result": customer}

    # --- list_customers -------------------------------------------------------
    if tool == "list_customers":
        status = args.get("status")
        limit = int(args.get("limit", 20))

        records = await asyncio.to_thread(fetch_customers, status, limit)

        await enqueue_event({
            "type": "audit",
            "tool": tool,
            "count": len(records)
        })
        return {"result": records}

    # --- update_customer ------------------------------------------------------
    if tool == "update_customer":
        cid = int(args.get("customer_id"))
        patch = args.get("data") or {}

        updated = await asyncio.to_thread(update_customer_record, cid, patch)

        if not updated:
            http_not_found("Customer not found for update")

        await enqueue_event({
            "type": "update",
            "tool": tool,
            "customer_id": updated["id"]
        })
        return {"result": updated}

    # --- create_ticket --------------------------------------------------------
    if tool == "create_ticket":
        cid = int(args.get("customer_id"))
        issue = str(args.get("issue"))
        priority = str(args.get("priority"))

        ticket = await asyncio.to_thread(create_ticket_record, cid, issue, priority)

        await enqueue_event({
            "type": "ticket",
            "tool": tool,
            "ticket_id": ticket["id"]
        })
        return {"result": ticket}

    # --- get_customer_history -------------------------------------------------
    if tool == "get_customer_history":
        cid = int(args.get("customer_id"))
        history = await asyncio.to_thread(fetch_history, cid)

        await enqueue_event({
            "type": "history",
            "tool": tool,
            "count": len(history)
        })
        return {"result": history}

    # unknown tool
    http_not_found(f"Unknown tool: {tool}")


@app.get("/events/stream")
async def stream_events():
    """
    SSE endpoint that streams queued events to any client.
    """

    async def generator():
        while True:
            event = await event_queue.get()
            yield {"event": "update", "data": event}

    return EventSourceResponse(generator())


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Simple liveness probe.
    """
    return {"status": "ok"}


# ----------------------------------------------------------------------------
#  Application Entrypoint
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
