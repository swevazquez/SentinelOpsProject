from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Callable, Literal
from uuid import uuid4

from services.agent.actions import ActionRequest


ApprovalDecision = Literal["approved", "denied"]
APPROVAL_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ApprovalError(PermissionError):
    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class ApprovalRecord:
    approval_id: str
    action_name: str
    arguments: dict[str, str]
    fingerprint: str
    status: str
    created_at: str
    expires_at: str
    decided_at: str | None = None
    consumed_at: str | None = None
    execution_reference: str | None = None

    def public_dict(self) -> dict[str, object]:
        return {
            "approval_id": self.approval_id,
            "action": self.action_name,
            "arguments": self.arguments,
            "fingerprint": self.fingerprint,
            "status": self.status,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "requires_approval": True,
            "impact": "Starts one predictive-maintenance workflow run.",
        }


class ApprovalStore:
    def __init__(
        self,
        project_root: Path,
        *,
        clock: Callable[[], datetime] = _utc_now,
        lifetime: timedelta = timedelta(minutes=10),
    ) -> None:
        self.storage_dir = project_root / "data" / "approvals"
        self._clock = clock
        self._lifetime = lifetime
        self._lock = Lock()

    def create(self, request: ActionRequest) -> ApprovalRecord:
        now = self._now()
        record = ApprovalRecord(
            approval_id=uuid4().hex,
            action_name=request.name,
            arguments=dict(request.arguments),
            fingerprint=request.fingerprint,
            status="pending",
            created_at=_timestamp(now),
            expires_at=_timestamp(now + self._lifetime),
        )
        with self._lock:
            self._write(record)
        return record

    def get(self, approval_id: str) -> ApprovalRecord:
        with self._lock:
            return self._read(approval_id)

    def decide(
        self,
        approval_id: str,
        decision: ApprovalDecision,
    ) -> ApprovalRecord:
        if decision not in ("approved", "denied"):
            raise ValueError(f"unsupported approval decision: {decision}")
        with self._lock:
            record = self._read(approval_id)
            self._assert_not_expired(record)
            if record.status != "pending":
                raise ApprovalError(
                    "already_decided",
                    f"approval request is already {record.status}",
                )
            updated = replace(
                record,
                status=decision,
                decided_at=_timestamp(self._now()),
            )
            self._write(updated)
            return updated

    def authorize(self, approval_id: str, request: ActionRequest) -> ApprovalRecord:
        with self._lock:
            record = self._read(approval_id)
            self._assert_not_expired(record)
            if record.status == "pending":
                raise ApprovalError("required", "action requires explicit approval")
            if record.status == "denied":
                raise ApprovalError("denied", "approval request was denied")
            if record.status == "consumed":
                raise ApprovalError("replayed", "approval request was already consumed")
            if record.status != "approved":
                raise ApprovalError("invalid_status", "approval request is not executable")
            if record.fingerprint != request.fingerprint:
                raise ApprovalError(
                    "mismatch",
                    "action does not match the approved request",
                )
            consumed = replace(
                record,
                status="consumed",
                consumed_at=_timestamp(self._now()),
            )
            self._write(consumed)
            return consumed

    def record_execution(self, approval_id: str, run_id: str) -> ApprovalRecord:
        with self._lock:
            record = self._read(approval_id)
            if record.status != "consumed":
                raise ApprovalError("invalid_status", "approval was not consumed")
            updated = replace(record, execution_reference=run_id)
            self._write(updated)
            return updated

    def _assert_not_expired(self, record: ApprovalRecord) -> None:
        if record.status == "expired":
            raise ApprovalError("expired", "approval request has expired")
        if record.status in ("pending", "approved") and self._now() >= _parse_timestamp(
            record.expires_at
        ):
            expired = replace(record, status="expired", decided_at=_timestamp(self._now()))
            self._write(expired)
            raise ApprovalError("expired", "approval request has expired")

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            raise ValueError("approval clock must return a timezone-aware datetime")
        return value.astimezone(UTC)

    def _path(self, approval_id: str) -> Path:
        if not APPROVAL_ID_PATTERN.fullmatch(approval_id):
            raise ValueError("approval_id must be a valid identifier")
        return self.storage_dir / f"approval_{approval_id}.json"

    def _read(self, approval_id: str) -> ApprovalRecord:
        path = self._path(approval_id)
        if not path.exists():
            raise LookupError(f"approval request not found: {approval_id}")
        return ApprovalRecord(**json.loads(path.read_text(encoding="utf-8")))

    def _write(self, record: ApprovalRecord) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        path = self._path(record.approval_id)
        temporary_path = path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps(asdict(record), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(path)


def _timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
