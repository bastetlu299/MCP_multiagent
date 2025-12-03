# Multi-Agent Customer Service System with MCP and A2A

This project implements 5 requirements:

- A fully functional MCP HTTP server exposing the five required database tools with SQLite storage and SSE streaming.
- Multiple independent A2A agents (Router via LangGraph, Customer Data Agent, Support Agent, Billing Agent) each running their own FastAPI + JSON-RPC server.
- A LangGraph-powered router agent that orchestrates multi-step workflows across specialists using real A2A requests.
- Demo utilities and setup instructions for running the stack locally.

## Project layout
```
/mcp_server          # FastAPI MCP server implementing tools/list and tools/call
/agents/router       # LangGraph router agent (A2A server)
/agents/data         # Customer Data Agent (calls MCP tools)
/agents/support      # Support Agent (non-billing support)
/agents/billing      # Billing Agent (optional specialist)
/shared              # Shared helpers (SQLite + A2A helpers)
requirements.txt     # Python dependencies
```

## Prerequisites
- Python 3.11+
- `pip install -r requirements.txt`

## Running the servers
Open separate terminals for each service (all uvicorn processes bind to `0.0.0.0`):

```bash
# 1) Start MCP server (tools/list, tools/call, SSE stream)
uvicorn mcp_server.app:app --port 8000 --reload

# 2) Customer Data Agent (calls MCP tools)
uvicorn agents.data.main:app --port 8011 --reload

# 3) Support Agent
uvicorn agents.support.main:app --port 8012 --reload

# 4) Billing Agent (optional)
uvicorn agents.billing.main:app --port 8013 --reload

# 5) LangGraph Router Agent
uvicorn agents.router.main:app --port 8010 --reload
```

## Demo script
With all services running, execute:

```bash
python demo.py "Need the history for customer 1"
```

The script will send a JSON-RPC `message/send` request to the router agent, which forwards to the data and support agents, then prints the aggregated response.

## MCP protocol support
- `GET /tools/list` returns all tool definitions and JSON schemas.
- `POST /tools/call` executes the requested tool.
- `GET /events/stream` provides a Server-Sent Events stream of tool calls for observability.

The MCP server uses SQLite and seeds example customers, tickets, and interactions on first start.

## A2A agent interoperability
Each agent exposes:
- Agent card at `/.well-known/agent.json`
- JSON-RPC endpoint at `/rpc` (supports `message/send` + streaming)
- Skills, capabilities, and metadata required by A2A clients (e.g., MCP Inspector, LangGraph flows).

Router coordination leverages LangGraph for conditional routing, multi-step workflows (data→support), and escalation to billing when keywords like "payment" or "refund" appear.

## Test scenarios
1. Simple Query: "Get customer information for ID 5"
Single agent, straightforward MCP call
2. Coordinated Query: "I'm customer 12345 and need help upgrading my account"
Multiple agents coordinate: data fetch + support response
3. Complex Query: "Show me all active customers who have open tickets"
Requires negotiation between data and support agents
4. Escalation: "I've been charged twice, please refund immediately!"
Router must identify urgency and route appropriately
5. Multi-Intent: "Update my email to new@email.com and show my ticket history"
Parallel task execution and coordination

## Notes
- Environment variables `MCP_SERVER_URL`, `DATA_AGENT_RPC`, `SUPPORT_AGENT_RPC`, and `BILLING_AGENT_RPC` let you repoint agents to different hosts.
- The shared SQLite database path defaults to `./database.sqlite` and will auto-initialize with seed data.
