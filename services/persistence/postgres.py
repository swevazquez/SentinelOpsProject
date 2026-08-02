from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row


MIGRATION_VERSION = "001_operational_persistence"
MIGRATION_PATH = Path(__file__).parent / "migrations" / f"{MIGRATION_VERSION}.sql"


class PersistenceUnavailableError(RuntimeError):
    """Raised when the configured persistence service cannot be used."""


@contextmanager
def postgres_connection(database_url: str) -> Iterator[Connection[dict]]:
    try:
        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            _apply_migration(connection)
            yield connection
    except psycopg.Error as exc:
        raise PersistenceUnavailableError(
            "PostgreSQL persistence is unavailable; the operation was not committed"
        ) from exc


def _apply_migration(connection: Connection[dict]) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS sentinelops_schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    applied = connection.execute(
        "SELECT 1 FROM sentinelops_schema_migrations WHERE version = %s",
        (MIGRATION_VERSION,),
    ).fetchone()
    if applied:
        return
    connection.execute(MIGRATION_PATH.read_text(encoding="utf-8"))
    connection.execute(
        """
        INSERT INTO sentinelops_schema_migrations (version)
        VALUES (%s)
        ON CONFLICT (version) DO NOTHING
        """,
        (MIGRATION_VERSION,),
    )
