"""
Shared compatibility package
----------------------------
Several agents still import helpers from ``shared.*`` even though the helpers
now live in :mod:`common`.  This module re-exports the legacy names so the
existing import statements continue to work without touching every agent.
"""

from .a2a_handler import SimpleAgentRequestHandler, register_agent_routes
from .message_utils import build_text_message

__all__ = [
    "SimpleAgentRequestHandler",
    "register_agent_routes",
    "build_text_message",
]
