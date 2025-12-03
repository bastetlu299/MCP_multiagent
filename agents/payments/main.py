"""
Payment / Billing Agent
-----------------------
Handles queries related to invoices, refunds, and general payment issues.
This agent does not call MCP tools directly; instead, it provides domain-
specific responses to upstream agents such as the router.
"""

from fastapi import FastAPI

from sdk.types import (
    AgentCard,
    AgentCapabilities,
    AgentProvider,
    AgentSkill,
    Message,
)
from shared.a2a_handler import SimpleAgentRequestHandler, register_agent_routes
from shared.message_utils import build_text_message


# ---------------------------------------------------------------------------
# Skill implementation
# ---------------------------------------------------------------------------

async def payment_skill(message: Message) -> Message:
    """
    Produce a text-based response summarizing billing capabilities.
    """
    user_text = message.parts[0].text if (message.parts and message.parts[0].text) else ""
    reply = (
        "Payment Agent Response:\n"
        "I handle refunds, invoice issues, failed payments, and account charges.\n"
        f"Your request: {user_text}"
    )
    return build_text_message(reply)


# ---------------------------------------------------------------------------
# Agent metadata
# ---------------------------------------------------------------------------

def create_agent_card() -> AgentCard:
    return AgentCard(
        name="Payment Agent",
        description="Provides assistance for payment, invoices, and refund inquiries.",
        version="1.0.0",
        url="http://localhost:8013",
        documentationUrl="https://example.com/docs/payments",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        provider=AgentProvider(
            organization="Assignment 5",
            url="http://localhost:8013",
        ),
        skills=[
            AgentSkill(
                id="payment",
                name="Payment Services",
                description="Supports billing problems and refund workflows.",
                tags=["billing", "payments"],
                inputModes=["text"],
                outputModes=["text"],
                examples=["Issue refund", "Send invoice", "Payment failed"],
            )
        ],
        preferredTransport="JSONRPC",
    )


# ---------------------------------------------------------------------------
# FastAPI app factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    app = FastAPI(title="Payment Agent Service")
    handler = SimpleAgentRequestHandler(
        agent_id="payment",
        skill_callback=payment_skill,
    )
    register_agent_routes(app, create_agent_card(), handler)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8013)
