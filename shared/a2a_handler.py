"""
Compatibility wrapper for ``common.a2a``.

Older parts of the assignment referenced ``shared.a2a_handler``. Rather than
updating every import, we provide this thin re-export so both names resolve to
the same implementation.
"""

from common.a2a import SimpleAgentRequestHandler, register_agent_routes

__all__ = ["SimpleAgentRequestHandler", "register_agent_routes"]
