"""
Compatibility helpers for message utilities.

Assignments referenced ``shared.message_utils.build_text_message`` even though
the implementation now resides in :mod:`common.message_utils`.  This module
bridges the gap without duplicating logic.
"""

from common.message_utils import create_text_message


def build_text_message(*args, **kwargs):
    """Backwards-compatible alias for :func:`create_text_message`."""
    return create_text_message(*args, **kwargs)


__all__ = ["build_text_message", "create_text_message"]
