"""
Async Database Utilities
------------------------
Provides asynchronous access to customer, ticket, and interaction data using
SQLite + aiosqlite. This module encapsulates schema initialization as well as
CRUD operations required by the MCP server and the A2A agents.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite


# ---------------------------------------------------------------------------
# Database configuration
# ---------------------------------------------------------------------------

DB_PATH = Path(os.getenv("A2A_DB_PATH", "./database.sqlite"))

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    issue TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    channel TEXT NOT NULL,
    notes TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(customer_id) REFERENCES customers(id)
);
"""

_SEED_CUSTOMERS = [
    ("Ana Customer", "ana@example.com", "active"),
    ("Brian Blocked", "brian@example.com", "delinquent"),
    ("Cara Care", "cara@example.com", "vip"),
]

_SEED_INTERACTIONS = [
    (1, "email", "Welcome email sent"),
    (1, "phone", "User reported login issue"),
    (2, "chat", "Billing dispute initiated"),
    (3, "email", "Requested feature roadmap"),
]


# ---------------------------------------------------------------------------
# Initialization helpers
# ---------------------------------------------------------------------------

async def initialize_database(db_path: Path = DB_PATH) -> None:
    """
    Create schema if needed and populate sample rows when database is empty.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        await db.executescript(_SCHEMA_SQL)
        await db.commit()

        # Only insert seed data on first run
        row_count = await db.execute_fetchone("SELECT COUNT(*) FROM customers")
        if row_count and row_count[0] == 0:
            await db.executemany(
                "INSERT INTO customers(name, email, status) VALUES (?, ?, ?)",
                _SEED_CUSTOMERS,
            )
            await db.executemany(
                "INSERT INTO interactions(customer_id, channel, notes) VALUES (?, ?, ?)",
                _SEED_INTERACTIONS,
            )
            await db.commit()


async def open_connection(db_path: Path = DB_PATH) -> aiosqlite.Connection:
    """
    Ensure the DB is initialized, then return a new connection.
    """
    await initialize_database(db_path)
    return await aiosqlite.connect(db_path)


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

async def get_customer(customer_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single customer by ID.
    """
    async with await open_connection() as db:
        row = await db.execute_fetchone(
            "SELECT id, name, email, status, created_at FROM customers WHERE id = ?",
            (customer_id,),
        )
        if not row:
            return None
        return {
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "status": row[3],
            "created_at": row[4],
        }


async def list_customers(status: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Retrieve multiple customers, optionally filtered by status.
    """
    async with await open_connection() as db:
        if status:
            rows = await db.execute_fetchall(
                "SELECT id, name, email, status, created_at "
                "FROM customers WHERE status = ? LIMIT ?",
                (status, limit),
            )
        else:
            rows = await db.execute_fetchall(
                "SELECT id, name, email, status, created_at "
                "FROM customers LIMIT ?",
                (limit,),
            )
        return [
            {
                "id": r[0],
                "name": r[1],
                "email": r[2],
                "status": r[3],
                "created_at": r[4],
            }
            for r in rows
        ]


async def update_customer(customer_id: int, changes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update allowed fields on a customer record.
    """
    allowed = {"name", "email", "status"}
    clean_updates = {k: v for k, v in changes.items() if k in allowed}

    existing = await get_customer(customer_id)
    if not existing:
        return None
    if not clean_updates:
        return existing

    async with await open_connection() as db:
        for col, value in clean_updates.items():
            await db.execute(
                f"UPDATE customers SET {col} = ? WHERE id = ?",
                (value, customer_id),
            )
        await db.commit()

    return await get_customer(customer_id)


async def create_ticket(customer_id: int, issue: str, priority: str) -> Dict[str, Any]:
    """
    Insert a new ticket and return the resulting row.
    """
    async with await open_connection() as db:
        cursor = await db.execute(
            "INSERT INTO tickets (customer_id, issue, priority, status) "
            "VALUES (?, ?, ?, 'open')",
            (customer_id, issue, priority),
        )
        await db.commit()
        ticket_id = cursor.lastrowid

        row = await db.execute_fetchone(
            "SELECT id, customer_id, issue, priority, status, created_at "
            "FROM tickets WHERE id = ?",
            (ticket_id,),
        )
        return {
            "id": row[0],
            "customer_id": row[1],
            "issue": row[2],
            "priority": row[3],
            "status": row[4],
            "created_at": row[5],
        }


async def list_interactions(customer_id: int) -> List[Dict[str, Any]]:
    """
    Return interaction history newest → oldest.
    """
    async with await open_connection() as db:
        rows = await db.execute_fetchall(
            "SELECT id, channel, notes, created_at "
            "FROM interactions WHERE customer_id = ? ORDER BY created_at DESC",
            (customer_id,),
        )
        return [
            {
                "id": r[0],
                "channel": r[1],
                "notes": r[2],
                "created_at": r[3],
            }
            for r in rows
        ]


async def add_interaction(customer_id: int, notes: str, channel: str = "agent") -> Dict[str, Any]:
    """
    Insert a new interaction entry and return it.
    """
    async with await open_connection() as db:
        cursor = await db.execute(
            "INSERT INTO interactions (customer_id, channel, notes) VALUES (?, ?, ?)",
            (customer_id, channel, notes),
        )
        await db.commit()
        new_id = cursor.lastrowid

        row = await db.execute_fetchone(
            "SELECT id, channel, notes, created_at "
            "FROM interactions WHERE id = ?",
            (new_id,),
        )

        return {
            "id": row[0],
            "channel": row[1],
            "notes": row[2],
            "created_at": row[3],
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "initialize_database",
    "open_connection",
    "get_customer",
    "list_customers",
    "update_customer",
    "create_ticket",
    "list_interactions",
    "add_interaction",
    "DB_PATH",
]
