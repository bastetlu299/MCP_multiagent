"""
Support Agent
-------------
Provides empathetic, user-facing support responses. If the message includes
data context forwarded by the router (e.g., “Data context: ...”), the agent
incorporates it into a more informed guidance message.
"""

from __future__ import annotations

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
# Internal helper functions
# ---------------------------------------------------------------------------

def parse_support_prompt(text: str) -> tuple[str, str]:
    """
    Extract optional upstream "data context" and the actual customer request.
    Router sends messages formatted like:
        "Data context: ... Now craft guidance..."
    Returns:
        (context_text, user_request)
    """
    if "Data context:" in text:
        parts = text.split("Data context:", 1)
        lead = parts[0].strip()
        context = parts[1].strip()
        request = lead if lead else "your request"
        return context, request

    cleaned = text.strip()
    return "", cleaned or "your request"


def generate_suggestions(user_prompt: str) -> list[str]:
    """
    Produce 2–3 practical next steps based on keywords in the request.
    """
    lower = user_prompt.lower()
    out: list[str] = []

    if any(k in lower for k in ["login", "password"]):
        out.append("Try resetting your password and confirm you can sign in from a trusted browser.")
        out.append("If it still fails, share the exact error message so we can diagnose quickly.")
    elif any(k in lower for k in ["ticket", "issue", "problem"]):
        out.append("I can open a support ticket and notify you as soon as there's progress.")
        out.append("Screenshots or timestamps would help us troubleshoot faster.")
    elif any(k in lower for k in ["history", "follow", "activity"]):
        out.append("I've reviewed your recent activity and will keep an eye on any new updates.")
        out.append("If something changes on your side, let me know and we can adjust next steps.")
    else:
        out.append("Tell me any specific details you'd like us to verify or double-check.")
        out.append("We can also set up a short follow-up if you need more help.")

    out.append("If this is urgent, reply here and I’ll jump on it immediately.")
    return out


# ---------------------------------------------------------------------------
# Skill implementation
# ---------------------------------------------------------------------------

async def support_skill(message: Message) -> Message:
    """
    Generate a friendly, end-user-facing support reply.
    This agent should never reveal internal routing or JSON structures.
    """
    text = message.parts[0].text if (message.parts and message.parts[0].text) else ""
    context_text, request_text = parse_support_prompt(text)

    # Greeting
    if context_text:
        opening = "Hi there — I reviewed the latest notes on your account."
    else:
        opening = "Hi there, thanks for reaching out."

    # Small contextual line
    prompt_lower = text.lower()
    if "login" in prompt_lower:
        context_line = "It looks like you're having trouble signing in."
    elif any(k in prompt_lower for k in ["ticket", "issue", "problem"]):
        context_line = "I can see you’re dealing with an issue that needs attention."
    elif context_text:
        context_line = "I’ve read through the account history you mentioned."
    else:
        context_line = ""

    # Build suggestions
    steps = generate_suggestions(text)

    response_lines = [
        opening,
        context_line,
        "",
        f"Here’s what I recommend based on {request_text}:",
    ]

    # Include top 3 suggestions
    for s in steps[:3]:
        response_lines.append(f"- {s}")

    response_lines.append(
        "If you'd like me to take action now, just reply to this message and I’ll handle it."
    )

    final_text = "\n".join(line for line in response_lines if line)
    return build_text_message(final_text)


# ---------------------------------------------------------------------------
# Agent metadata
# ---------------------------------------------------------------------------

def create_agent_card() -> AgentCard:
    return AgentCard(
        name="Support Agent",
        description="Provides troubleshooting help and customer-friendly guidance.",
        url="http://localhost:8012",
        version="1.0.0",
        documentationUrl="https://example.com/docs/support",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        provider=AgentProvider(
            organization="Assignment 5",
            url="http://localhost:8012",
        ),
        skills=[
            AgentSkill(
                id="support-general",
                name="General Support",
                description="Handles everyday support inquiries and troubleshooting questions.",
                tags=["support", "triage", "helpdesk"],
                inputModes=["text"],
                outputModes=["text"],
                examples=[
                    "Help me reset my password",
                    "I need to troubleshoot an issue",
                    "Review my recent activity",
                ],
            )
        ],
        preferredTransport="JSONRPC",
    )


# ---------------------------------------------------------------------------
# FastAPI app factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    app = FastAPI(title="Support Agent Service")
    handler = SimpleAgentRequestHandler(
        agent_id="support",
        skill_callback=support_skill,
    )
    register_agent_routes(app, create_agent_card(), handler)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8012)
