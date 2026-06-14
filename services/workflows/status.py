from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal


LOGGER = logging.getLogger(__name__)
WorkflowState = Literal["running", "completed", "failed"]


@dataclass(frozen=True)
class WorkflowStatus:
    run_id: str
    status: WorkflowState
    updated_at: str
    step: str | None = None
    error: str | None = None


def record_workflow_status(
    *,
    project_root: Path,
    run_id: str,
    status: WorkflowState,
    step: str | None = None,
    error: str | None = None,
) -> Path:
    record = WorkflowStatus(
        run_id=run_id,
        status=status,
        updated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        step=step,
        error=error,
    )
    output_dir = project_root / "data" / "workflow-status"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"workflow_{run_id}.json"
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
