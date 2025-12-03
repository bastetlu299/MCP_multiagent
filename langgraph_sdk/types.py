"""
sdk.types
---------
Core data structures shared across A2A agents, the router workflow, and the MCP
server interface. These models describe messages, tasks, capabilities, and agent
metadata used throughout the system.

All models are intentionally lightweight Pydantic BaseModels so they can be
serialized cleanly over JSON-RPC or HTTP, matching the A2A protocol style.
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Message primitives
# ---------------------------------------------------------------------------

class Role(str, Enum):
    """Indicates whether a message is authored by the user or an agent."""
    user = "user"
    agent = "agent"


class TextPart(BaseModel):
    """A single text fragment contained within a message."""
    text: str


class Message(BaseModel):
    """
    A message exchanged between agents or between router and agents.
    Each message may contain multiple text parts and optionally reference
    an active task via taskId or contextId.
    """
    messageId: str = Field(default_factory=lambda: uuid.uuid4().hex)
    role: Role
    parts: List[TextPart]
    taskId: Optional[str] = None
    contextId: Optional[str] = None


# ---------------------------------------------------------------------------
# Task-related models
# ---------------------------------------------------------------------------

class TaskState(str, Enum):
    """Lifecycle states for asynchronous tasks."""
    running = "running"
    completed = "completed"
    canceled = "canceled"


class TaskStatus(BaseModel):
    """A wrapper for a task’s current state and optional message output."""
    state: TaskState
    message: Optional[Message] = None


class Task(BaseModel):
    """
    Represents a full task instance, including its history and current status.
    The router and remote agents use this when returning results.
    """
    id: str
    contextId: str
    history: List[Message]
    status: TaskStatus


class TaskStatusUpdateEvent(BaseModel):
    """Event object pushed when a task reaches a new state."""
    taskId: str
    contextId: str
    status: TaskStatus
    final: bool


# alias used by the system where events are expected
Event = TaskStatusUpdateEvent


# ---------------------------------------------------------------------------
# Task-management request/response models
# ---------------------------------------------------------------------------

class TaskPushNotificationConfig(BaseModel):
    """Configuration entry for push notification settings on a task."""
    task_id: str
    push_notification_config: Dict[str, Any]


class TaskQueryParams(BaseModel):
    id: str


class TaskIdParams(BaseModel):
    id: str


class MessageSendParams(BaseModel):
    """Payload used when sending a Message over JSON-RPC."""
    message: Message


class GetTaskPushNotificationConfigParams(BaseModel):
    id: str


class ListTaskPushNotificationConfigParams(BaseModel):
    limit: Optional[int] = None


class DeleteTaskPushNotificationConfigParams(BaseModel):
    id: str


# ---------------------------------------------------------------------------
# Agent metadata structures
# ---------------------------------------------------------------------------

class AgentSkill(BaseModel):
    """
    Defines a single skill offered by an agent. A skill is a functional
    capability that accepts text input and generates text output.
    """
    id: str
    name: str
    description: str
    tags: List[str]
    inputModes: List[str]
    outputModes: List[str]
    examples: List[str]


class AgentCapabilities(BaseModel):
    """
    Features supported by the agent, such as streaming or multimodal support.
    Currently streaming=True is sufficient for A2A interoperability.
    """
    streaming: bool = True


class AgentProvider(BaseModel):
    """Metadata describing the organization or service hosting the agent."""
    organization: str
    url: str


class AgentCard(BaseModel):
    """
    Full metadata record for an agent. Used by the router and other remote
    systems to understand what the agent can do and how it should be invoked.
    """
    name: str
    description: str
    url: str
    version: str
    skills: List[AgentSkill]
    defaultInputModes: List[str]
    defaultOutputModes: List[str]
    capabilities: AgentCapabilities
    provider: AgentProvider
    documentationUrl: Optional[str] = None
    preferredTransport: Optional[str] = None


# ---------------------------------------------------------------------------
# Public API for this module
# ---------------------------------------------------------------------------

__all__ = [
    "AgentCard",
    "AgentCapabilities",
    "AgentProvider",
    "AgentSkill",
    "DeleteTaskPushNotificationConfigParams",
    "Event",
    "GetTaskPushNotificationConfigParams",
    "ListTaskPushNotificationConfigParams",
    "Message",
    "MessageSendParams",
    "Role",
    "Task",
    "TaskIdParams",
    "TaskPushNotificationConfig",
    "TaskQueryParams",
    "TaskState",
    "TaskStatus",
    "TaskStatusUpdateEvent",
    "TextPart",
]
