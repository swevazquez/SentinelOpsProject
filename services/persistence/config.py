from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Literal


PersistenceBackend = Literal["file", "postgres"]
BACKEND_ENV = "SENTINELOPS_PERSISTENCE_BACKEND"
DATABASE_URL_ENV = "DATABASE_URL"


class PersistenceConfigurationError(RuntimeError):
    """Raised when the selected persistence backend is not configured."""


@dataclass(frozen=True)
class PersistenceSettings:
    backend: PersistenceBackend
    database_url: str | None


def persistence_settings() -> PersistenceSettings:
    backend = os.getenv(BACKEND_ENV, "file").strip().lower()
    if backend not in ("file", "postgres"):
        raise PersistenceConfigurationError(
            f"{BACKEND_ENV} must be either 'file' or 'postgres'"
        )
    database_url = os.getenv(DATABASE_URL_ENV)
    if backend == "postgres" and not database_url:
        raise PersistenceConfigurationError(
            f"{DATABASE_URL_ENV} is required when {BACKEND_ENV}=postgres"
        )
    return PersistenceSettings(
        backend=backend,
        database_url=database_url,
    )


def prediction_storage_dir(project_root: Path) -> Path:
    return project_root / "data" / "predictions"
