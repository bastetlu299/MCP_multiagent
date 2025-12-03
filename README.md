# MCP Multi-Agent System

A comprehensive multi-agent architecture built on Model Context Protocol (MCP) and A2A (Agent-to-Agent) communication. This system coordinates specialized agents (Data, Support, Payment) through a Router agent to handle customer support scenarios.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP Server (Port 8000)                  │
│              SQLite Database + Tool Registry                │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ HTTP/REST
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Data Agent   │    │Support Agent │    │Payment Agent │
│ (Port 8011)  │    │ (Port 8012)  │    │ (Port 8013)  │
└──────────────┘    └──────────────┘    └──────────────┘
        ▲                   ▲                   ▲
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │ A2A RPC
                            │
                    ┌───────▼────────┐
                    │ Router Agent   │
                    │  (Port 8010)   │
                    └────────────────┘
```

## Project Structure

```
.
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── database_setup.py              # SQLite initialization
├── demo.py                        # Example client
├── common/                        # Shared utilities
│   ├── a2a.py                    # A2A runtime & JSON-RPC
│   ├── db.py                     # Async database helpers
│   ├── message_utils.py          # Message construction
│   └── __init__.py
├── sdk/                           # Core data types
│   ├── types.py                  # Pydantic models
│   ├── agent.py                  # Agent types
│   ├── task.py                   # Task management
│   └── __init__.py
├── shared/                        # Backwards compatibility
│   ├── a2a_handler.py            # Re-exports from common
│   ├── message_utils.py          # Re-exports from common
│   └── __init__.py
├── mcp_server/                    # MCP Server (Port 8000)
│   ├── app.py                    # FastAPI application
│   ├── database.py               # Database interface
│   └── __init__.py
└── agents/                        # Specialized agents
    ├── router/                   # Router Agent (Port 8010)
    │   ├── main.py              # LangGraph workflow
    │   └── __init__.py
    ├── data/                     # Data Agent (Port 8011)
    │   ├── main.py              # MCP client for records
    │   └── __init__.py
    ├── support/                  # Support Agent (Port 8012)
    │   ├── main.py              # Customer guidance
    │   └── __init__.py
    ├── payments/                 # Payment Agent (Port 8013)
    │   ├── main.py              # Billing responses
    │   └── __init__.py
    └── __init__.py
```

## Setup Instructions

### Prerequisites

- Python 3.10+
- `pip` and virtual environment support

### 1. Clone & Navigate to Project

```bash
cd /path/to/MCP_multiagent
```

### 2. Create Virtual Environment

```bash
# Create isolated Python environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**What's in `requirements.txt`:**

- **FastAPI / Uvicorn**: Web framework for agents and MCP server
- **LangGraph**: Workflow orchestration for the router
- **HTTPx**: Async HTTP client for A2A communication
- **aiosqlite**: Async SQLite driver
- **Pydantic**: Data validation
- **python-dotenv**: Environment configuration
- **sse-starlette**: Server-Sent Events for real-time updates
- Additional utilities (orjson, fastmcp, etc.)

### 4. Initialize Database

```bash
python database_setup.py
```

Creates `support.db` with sample customers and interactions.

### 5. Start All Services

**Terminal 1 — MCP Server:**
```bash
python -m mcp_server.app
# Listens on http://localhost:8000
```

**Terminal 2 — Data Agent:**
```bash
python -m agents.data.main
# Listens on http://localhost:8011
```

**Terminal 3 — Support Agent:**
```bash
python -m agents.support.main
# Listens on http://localhost:8012
```

**Terminal 4 — Payment Agent:**
```bash
python -m agents.payments.main
# Listens on http://localhost:8013
```

**Terminal 5 — Router Agent:**
```bash
python -m agents.router.main
# Listens on http://localhost:8010
```

### 6. Test the System

In a new terminal (with `venv` activated):

```bash
python demo.py
```

Or run Jupyter scenarios:

```bash
jupyter notebook Assignment5_notebook.ipynb
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database path (default: ./database.sqlite)
A2A_DB_PATH=./database.sqlite

# MCP Server URL (for agents to reach it)
MCP_SERVER_URL=http://localhost:8000

# Agent RPC endpoints (used by router)
DATA_AGENT_RPC=http://localhost:8011/rpc
SUPPORT_AGENT_RPC=http://localhost:8012/rpc
BILLING_AGENT_RPC=http://localhost:8013/rpc

# Router endpoint (used by clients)
ROUTER_RPC=http://localhost:8010/rpc
```

Load environment file:
```bash
export $(cat .env | xargs)
```

## API Overview

### MCP Server Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/tools/list` | GET | List available tools |
| `/tools/call` | POST | Invoke a tool |
| `/events/stream` | GET | Stream audit events (SSE) |
| `/health` | GET | Health check |

**Available Tools:**
- `get_customer` — Fetch customer record by ID
- `list_customers` — List customers (optionally filtered by status)
- `update_customer` — Modify customer fields
- `create_ticket` — Open a support ticket
- `get_customer_history` — Retrieve interaction history

### A2A Agent RPC Methods

All agents support JSON-RPC 2.0:

```json
{
  "jsonrpc": "2.0",
  "id": "unique-id",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "uuid",
      "role": "user",
      "parts": [{"text": "Your query here"}]
    }
  }
}
```

**Methods:**
- `message/send` — Synchronous request
- `message/send_stream` — Streaming response
- `task/get` — Retrieve task by ID
- `task/cancel` — Cancel a running task

### Agent Metadata

Each agent exposes metadata at `/.well-known/agent-card.json`:

```bash
curl http://localhost:8010/.well-known/agent-card.json
```

Returns agent name, capabilities, skills, and documentation URL.

## Usage Examples

### 1. Query Customer Data

```python
import asyncio
import httpx
from sdk.types import Message, MessageSendParams, Role
from common.message_utils import create_text_message

async def query_router():
    msg = create_text_message("Get customer information for ID 5", role=Role.user)
    params = {"message": msg.model_dump()}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8010/rpc",
            json={
                "jsonrpc": "2.0",
                "id": "demo",
                "method": "message/send",
                "params": params
            }
        )
    
    result = response.json()
    print(result["result"]["status"]["message"]["parts"][0]["text"])

asyncio.run(query_router())
```

### 2. Multi-Intent Scenario

```python
query = "Update my email to newemail@example.com and show my ticket history"
# Router automatically routes to both Data and Support agents
# Combines responses into a single coherent answer
```

### 3. Escalation Flow

```python
query = "I've been charged twice, please refund immediately!"
# Router detects billing keywords → routes to Payment agent
# Payment agent provides specialized response
```

## Workflow: Request Flow

1. **Client Request** → Router Agent (`:8010/rpc`)
2. **Router Intent Classification** → Determines which specialist(s) to call
3. **Specialist Invocation** → Data/Support/Payment agents respond via A2A RPC
4. **Response Aggregation** → Router combines specialist outputs
5. **Final Response** → Returned to client with unified message

### Routing Logic

| Query Keywords | Route | Agents |
|---|---|---|
| `billing`, `refund`, `payment` | Payment | Payment Agent |
| `customer`, `history` | Data then Support | Data Agent → Support Agent |
| Default | Support | Support Agent |

## Database Schema

### customers
```sql
CREATE TABLE customers (
  id INTEGER PRIMARY KEY,
  name TEXT,
  email TEXT,
  status TEXT,  -- 'active', 'delinquent', 'vip'
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### tickets
```sql
CREATE TABLE tickets (
  id INTEGER PRIMARY KEY,
  customer_id INTEGER,
  issue TEXT,
  priority TEXT,
  status TEXT DEFAULT 'open',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### interactions
```sql
CREATE TABLE interactions (
  id INTEGER PRIMARY KEY,
  customer_id INTEGER,
  channel TEXT,  -- 'email', 'phone', 'chat'
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## Deactivating Virtual Environment

When done:

```bash
deactivate
```

## Troubleshooting

### Port Already in Use
```bash
# Kill existing process on port (e.g., 8010)
lsof -i :8010 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### Database Lock
```bash
# Remove stale database
rm -f support.db database.sqlite
python database_setup.py
```

### Import Errors
```bash
# Ensure you're in venv and installed dependencies
source venv/bin/activate
pip install -r requirements.txt
```

### Agents Can't Connect
- Verify all services are running on expected ports
- Check `.env` contains correct endpoint URLs
- Test connectivity: `curl http://localhost:8000/health`

## Key Features

✅ **Modular Architecture** — Each agent is independently deployable  
✅ **LangGraph Orchestration** — Router uses state graphs for complex workflows  
✅ **A2A Protocol** — Standard JSON-RPC for inter-agent communication  
✅ **MCP Integration** — Agents delegate data operations to centralized MCP server  
✅ **Async/Await** — Full async support for concurrent operations  
✅ **Pydantic Validation** — Type-safe message passing  
✅ **Real-time Events** — SSE streaming for audit logs and updates  

## Testing

Run the included Jupyter notebook:

```bash
jupyter notebook Assignment5_notebook.ipynb
```

Or execute demo scenarios:

```bash
python demo.py
```

This tests:
- Simple customer lookups
- Multi-agent coordination
- Complex search queries
- Escalation workflows
- Multi-intent requests

## Performance Notes

- **Database**: SQLite with `aiosqlite` for async access
- **Concurrency**: Agent requests are non-blocking via httpx
- **Memory**: Tasks stored in-memory; consider persistent storage for production
- **Scalability**: Current design suitable for small-to-medium deployments

## License

Assignment 5 — Educational project

## Support

For issues or questions, refer to:
- [Assignment5_notebook.ipynb](Assignment5_notebook.ipynb) — Full scenario walkthrough
- [demo.py](demo.py) — Working examples
- Individual agent `main.py` files for implementation details

---

**Last Updated**: December 2025  
**Python Version**: 3.10+  
**Status**: ✅ Production-ready