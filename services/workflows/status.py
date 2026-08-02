from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Protocol, cast

from services.persistence.config import persistence_settings
from services.persistence.postgres import postgres_connection


LOGGER = logging.getLogger(__name__)
WorkflowState = Literal["running", "completed", "failed"]
STATUS_STORAGE_DIR = Path("data/workflow-status")


@dataclass(frozen=True)
class WorkflowStatus:
    run_id: str
    status: WorkflowState
    updated_at: str
    step: str | None = None
    error: str | None = None
    approval_id: str | None = None


@dataclass(frozen=True)
class WorkflowStatusSummary:
    total: int
    running: int
    completed: int
    failed: int


class WorkflowStatusRepository(Protocol):
    def save(self, status: WorkflowStatus) -> Path | None: ...

    def get(self, run_id: str) -> WorkflowStatus | None: ...

    def list(self) -> list[WorkflowStatus]: ...


def _validate_run_id(run_id: str) -> None:
    if not run_id or any(character in run_id for character in ("/", "\\", "..")):
        raise ValueError("run_id must be a non-empty file-safe value")


def _validate_status(status: WorkflowStatus) -> None:
    _validate_run_id(status.run_id)
    if status.status not in ("running", "completed", "failed"):
        raise ValueError(f"unsupported workflow status: {status.status}")
    if not status.updated_at.endswith("Z"):
        raise ValueError("workflow status updated_at must be a UTC timestamp")


class JsonWorkflowStatusRepository:
    def __init__(self, project_root: Path) -> None:
        self.output_dir = project_root / STATUS_STORAGE_DIR

    def save(self, status: WorkflowStatus) -> Path:
        _validate_status(status)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"workflow_{status.run_id}.json"
        temporary_path = output_path.with_suffix(".json.tmp")
        temporary_path.write_text(
            json.dumps(asdict(status), indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(output_path)
        return output_path

    def get(self, run_id: str) -> WorkflowStatus | None:
        path = self._status_path(run_id)
        if not path.exists():
            return None
        return _load_status_file(path)

    def list(self) -> list[WorkflowStatus]:
        if not self.output_dir.exists():
            return []
        statuses = [
            _load_status_file(path)
            for path in sorted(self.output_dir.glob("workflow_*.json"))
        ]
        return sorted(statuses, key=lambda status: status.updated_at, reverse=True)

    def _status_path(self, run_id: str) -> Path:
        _validate_run_id(run_id)
        return self.output_dir / f"workflow_{run_id}.json"


class PostgresWorkflowStatusRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def save(self, status: WorkflowStatus) -> None:
        _validate_status(status)
        with postgres_connection(self.database_url) as connection:
            connection.execute(
                """
                INSERT INTO sentinelops_workflow_status (
                    run_id, status, updated_at, step, error, approval_id
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (run_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at,
                    step = EXCLUDED.step,
                    error = EXCLUDED.error,
                    approval_id = EXCLUDED.approval_id
                """,
                (
                    status.run_id,
                    status.status,
                    status.updated_at,
                    status.step,
                    status.error,
                    status.approval_id,
                ),
            )
        return None

    def get(self, run_id: str) -> WorkflowStatus | None:
        _validate_run_id(run_id)
        with postgres_connection(self.database_url) as connection:
            record = connection.execute(
                """
                SELECT run_id, status, updated_at, step, error, approval_id
                FROM sentinelops_workflow_status
                WHERE run_id = %s
                """,
                (run_id,),
            ).fetchone()
        return _status_from_record(record) if record else None

    def list(self) -> list[WorkflowStatus]:
        with postgres_connection(self.database_url) as connection:
            records = connection.execute(
                """
                SELECT run_id, status, updated_at, step, error, approval_id
                FROM sentinelops_workflow_status
                ORDER BY updated_at DESC
                """
            ).fetchall()
        return [_status_from_record(record) for record in records]


def _status_from_record(record: dict[str, object]) -> WorkflowStatus:
    status = WorkflowStatus(
        run_id=str(record["run_id"]),
        status=cast(WorkflowState, str(record["status"])),
        updated_at=str(record["updated_at"]),
        step=str(record["step"]) if record["step"] is not None else None,
        error=str(record["error"]) if record["error"] is not None else None,
        approval_id=(
            str(record["approval_id"])
            if record["approval_id"] is not None
            else None
        ),
    )
    _validate_status(status)
    return status


def workflow_status_repository(project_root: Path) -> WorkflowStatusRepository:
    settings = persistence_settings()
    if settings.backend == "postgres":
        assert settings.database_url is not None
        return PostgresWorkflowStatusRepository(settings.database_url)
    return JsonWorkflowStatusRepository(project_root)


def record_workflow_status(
    *,
    project_root: Path,
    run_id: str,
    status: WorkflowState,
    step: str | None = None,
    error: str | None = None,
    approval_id: str | None = None,
) -> Path | None:
    repository = workflow_status_repository(project_root)
    if approval_id is None:
        existing = repository.get(run_id)
        if existing is not None:
            approval_id = existing.approval_id
    record = WorkflowStatus(
        run_id=run_id,
        status=status,
        updated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        step=step,
        error=error,
        approval_id=approval_id,
    )
    output_path = repository.save(record)

    log = LOGGER.error if status == "failed" else LOGGER.info
    log(
        "workflow run_id=%s status=%s step=%s error=%s",
        run_id,
        status,
        step or "-",
        error or "-",
    )
    return output_path


def _load_status_file(path: Path) -> WorkflowStatus:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required_fields = {"run_id", "status", "updated_at"}
    missing_fields = sorted(
        field
        for field in required_fields
        if field not in payload or payload[field] == ""
    )
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise ValueError(f"workflow status missing required fields: {missing}")

    status = WorkflowStatus(
        run_id=payload["run_id"],
        status=payload["status"],
        updated_at=payload["updated_at"],
        step=payload.get("step"),
        error=payload.get("error"),
        approval_id=payload.get("approval_id"),
    )
    _validate_status(status)
    return status


def get_workflow_status(project_root: Path, run_id: str) -> WorkflowStatus | None:
    return workflow_status_repository(project_root).get(run_id)


def list_workflow_statuses(project_root: Path) -> list[WorkflowStatus]:
    return workflow_status_repository(project_root).list()


def summarize_workflow_statuses(project_root: Path) -> WorkflowStatusSummary:
    statuses = list_workflow_statuses(project_root)
    return WorkflowStatusSummary(
        total=len(statuses),
        running=sum(status.status == "running" for status in statuses),
        completed=sum(status.status == "completed" for status in statuses),
        failed=sum(status.status == "failed" for status in statuses),
    )
