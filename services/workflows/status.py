from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal


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


def record_workflow_status(
    *,
    project_root: Path,
    run_id: str,
    status: WorkflowState,
    step: str | None = None,
    error: str | None = None,
    approval_id: str | None = None,
) -> Path:
    output_dir = project_root / STATUS_STORAGE_DIR
    output_path = output_dir / f"workflow_{run_id}.json"
    if approval_id is None and output_path.exists():
        approval_id = _load_status_file(output_path).approval_id
    record = WorkflowStatus(
        run_id=run_id,
        status=status,
        updated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        step=step,
        error=error,
        approval_id=approval_id,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(asdict(record), indent=2) + "\n",
        encoding="utf-8",
    )

    log = LOGGER.error if status == "failed" else LOGGER.info
    log(
        "workflow run_id=%s status=%s step=%s error=%s",
        run_id,
        status,
        step or "-",
        error or "-",
    )
    return output_path


def _status_path(project_root: Path, run_id: str) -> Path:
    if not run_id or any(character in run_id for character in ("/", "\\", "..")):
        raise ValueError("run_id must be a non-empty file-safe value")
    return project_root / STATUS_STORAGE_DIR / f"workflow_{run_id}.json"


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

    if payload["status"] not in ("running", "completed", "failed"):
        raise ValueError(f"unsupported workflow status: {payload['status']}")

    if not str(payload["updated_at"]).endswith("Z"):
        raise ValueError("workflow status updated_at must be a UTC timestamp")

    return WorkflowStatus(
        run_id=payload["run_id"],
        status=payload["status"],
        updated_at=payload["updated_at"],
        step=payload.get("step"),
        error=payload.get("error"),
        approval_id=payload.get("approval_id"),
    )


def get_workflow_status(project_root: Path, run_id: str) -> WorkflowStatus | None:
    path = _status_path(project_root, run_id)
    if not path.exists():
        return None
    return _load_status_file(path)


def list_workflow_statuses(project_root: Path) -> list[WorkflowStatus]:
    status_dir = project_root / STATUS_STORAGE_DIR
    if not status_dir.exists():
        return []

    statuses = [
        _load_status_file(path)
        for path in sorted(status_dir.glob("workflow_*.json"))
    ]
    return sorted(statuses, key=lambda status: status.updated_at, reverse=True)


def summarize_workflow_statuses(project_root: Path) -> WorkflowStatusSummary:
    statuses = list_workflow_statuses(project_root)
    return WorkflowStatusSummary(
        total=len(statuses),
        running=sum(status.status == "running" for status in statuses),
        completed=sum(status.status == "completed" for status in statuses),
        failed=sum(status.status == "failed" for status in statuses),
    )
