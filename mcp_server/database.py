"""
Database interface layer used by the MCP server and A2A agents.

This module centralizes all data reads/writes to the SQLite database,
providing a clean API for the MCP tool handlers to interact with customers,
tickets, and interaction history.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from database_setup import DatabaseSetup


# -----------------------------------------------------------------------------
#  Database initialization & configuration
# -----------------------------------------------------------------------------

_setup = DatabaseSetup()
_setup.initialize()  # ensures the DB file + schema exist
DB_PATH: Path = _setup.db_path


def _open_db() -> sqlite3.Connection:
    """
    Return a SQLite connection with row access configured as dict-like objects.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# -----------------------------------------------------------------------------
#  Query Functions
# -----------------------------------------------------------------------------

def get_customer(customer_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch a single customer record by ID.
    """
    with _open_db() as db:
        row = db.execute(
            """
            SELECT id, name, email, status, created_at
            FROM customers
            WHERE id = ?
            """,
            (customer_id,),
        ).fetchone()
        return dict(row) if row else None


def list_customers(status: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Retrieve multiple customers, optionally filtered by status.
    """
    with _open_db() as db:
        if status:
            rows = db.execute(
                """
                SELECT id, name, email, status, created_at
                FROM customers
                WHERE status = ?
                LIMIT ?
                """,
                (status, limit),
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT id, name, email, status, created_at
                FROM customers
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(r) for r in rows]


def modify_customer(customer_id: int, changes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update permitted customer fields. Returns updated record or None if missing.
    """
    allowed = {"name", "email", "status"}
    updates = {k: v for k, v in changes.items() if k in allowed}

    # nothing to update → return original
    if not updates:
        return get_customer(customer_id)

    with _open_db() as db:
        exists = db.execute(
            "SELECT 1 FROM customers WHERE id = ?", (customer_id,)
        ).fetchone()
        if not exists:
            return None

        assignments = ", ".join([f"{col} = ?" for col in updates])
        values = list(updates.values()) + [customer_id]

        db.execute(
            f"UPDATE customers SET {assignments} WHERE id = ?",
            values,
        )
        db.commit()

    return get_customer(customer_id)


def new_ticket(customer_id: int, issue: str, priority: str) -> Dict[str, Any]:
    """
    Insert a new support ticket and return the full ticket entry.
    """
    with _open_db() as db:
        cur = db.execute(
            """
            INSERT INTO tickets (customer_id, issue, priority, status)
            VALUES (?, ?, ?, 'open')
            """,
            (customer_id, issue, priority),
        )
        ticket_id = cur.lastrowid
        db.commit()

        row = db.execute(
            """
            SELECT id, customer_id, issue, priority, status, created_at
            FROM tickets
            WHERE id = ?
            """,
            (ticket_id,),
        ).fetchone()

        return dict(row)


def customer_history(customer_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve interaction records for a customer, newest first.
    """
    with _open_db() as db:
        rows = db.execute(
            """
            SELECT id, channel, notes, created_at
            FROM interactions
            WHERE customer_id = ?
            ORDER BY created_at DESC
            """,
            (customer_id,),
        ).fetchall()

        return [dict(r) for r in rows]


# -----------------------------------------------------------------------------
#  Backwards-compatible aliases for legacy imports
# -----------------------------------------------------------------------------

def fetch_customer(customer_id: int) -> Optional[Dict[str, Any]]:
    return get_customer(customer_id)


def fetch_customers(status: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    return list_customers(status=status, limit=limit)


def update_customer_record(customer_id: int, changes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return modify_customer(customer_id, changes)


def create_ticket_record(customer_id: int, issue: str, priority: str) -> Dict[str, Any]:
    return new_ticket(customer_id, issue, priority)


def fetch_history(customer_id: int) -> List[Dict[str, Any]]:
    return customer_history(customer_id)


# -----------------------------------------------------------------------------
#  Public API for import
# -----------------------------------------------------------------------------

__all__ = [
    "DB_PATH",
    "get_customer",
    "list_customers",
    "modify_customer",
    "new_ticket",
    "customer_history",
    "fetch_customer",
    "fetch_customers",
    "update_customer_record",
    "create_ticket_record",
    "fetch_history",
]
