"""
Message Utilities
-----------------
Utility helpers for constructing A2A Message objects. All agents use these
helpers to produce consistent message structures for JSON-RPC responses.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sdk.types import Message, Role, TextPart


def create_text_message(
    text: str,
    *,
    role: Role = Role.agent,
    task_id: Optional[str] = None,
    context_id: Optional[str] = None,
) -> Message:
    """
    Create a standardized text-only Message object.

    Args:
        text: The textual content to embed in the message.
        role: Whether the message originates from the agent or user.
        task_id: Optional task identifier assigned by the runtime.
        context_id: Optional context identifier for multi-step flows.

    Returns:
        A fully constructed Message with a unique messageId.
    """

    part = TextPart(text=text)

    return Message(
        messageId=uuid.uuid4().hex,
        role=role,
        parts=[part],
        taskId=task_id,
        contextId=context_id,
    )
