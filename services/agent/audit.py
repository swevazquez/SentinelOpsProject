from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


SAFE_LABEL = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
SAFE_ERROR_CATEGORY = re.compile(r"^(?:[A-Za-z0-9_.-]{1,64}|http_[1-5][0-9]{2})$")


@dataclass(frozen=True)
class AgentAuditEvent:
    timestamp: str
    correlation_id: str
    operation_type: str
    operation_name: str
    outcome: str
    duration_ms: float
    error_category: str | None = None


class AgentAuditLogger:
    def __init__(self, path: Path) -> None:
        self.path = path

    def record(
        self,
        *,
        correlation_id: str,
        operation_type: str,
        operation_name: str,
        outcome: str,
        duration_ms: float,
        error_category: str | None = None,
    ) -> AgentAuditEvent:
        event = AgentAuditEvent(
            timestamp=datetime.now(UTC).isoformat(),
            correlation_id=_safe_label(correlation_id, "invalid_correlation_id"),
            operation_type=_safe_label(operation_type, "invalid_operation_type"),
            operation_name=_safe_operation_name(operation_name),
            outcome=_safe_label(outcome, "invalid_outcome"),
            duration_ms=round(max(duration_ms, 0), 3),
            error_category=_safe_error_category(error_category),
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(asdict(event), sort_keys=True) + "\n")
        return event


def default_audit_logger(project_root: Path) -> AgentAuditLogger:
    return AgentAuditLogger(project_root / "data" / "audit" / "agent-operations.jsonl")


def _safe_operation_name(value: str) -> str:
    return _safe_label(value, "invalid_operation_name")


def _safe_label(value: str, fallback: str) -> str:
    if isinstance(value, str) and SAFE_LABEL.fullmatch(value):
        return value
    return fallback


def _safe_error_category(value: str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str) and SAFE_ERROR_CATEGORY.fullmatch(value):
        return value
    return "invalid_error_category"
