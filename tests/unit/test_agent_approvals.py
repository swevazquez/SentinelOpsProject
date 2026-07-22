from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from services.agent.actions import prepare_action_request
from services.agent.approvals import ApprovalError, ApprovalStore


class MutableClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value


class AgentApprovalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temporary_directory.name)
        self.clock = MutableClock(datetime(2026, 7, 22, 12, 0, tzinfo=UTC))
        self.store = ApprovalStore(
            self.project_root,
            clock=self.clock,
            lifetime=timedelta(minutes=10),
        )
        self.request = prepare_action_request(
            action_name="start_workflow",
            arguments={"workflow": "predictive-maintenance"},
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_pending_and_denied_requests_cannot_be_consumed(self) -> None:
        pending = self.store.create(self.request)
        with self.assertRaisesRegex(ApprovalError, "explicit approval"):
            self.store.authorize(pending.approval_id, self.request)

        denied = self.store.decide(pending.approval_id, "denied")
        self.assertEqual(denied.status, "denied")
        with self.assertRaisesRegex(ApprovalError, "was denied"):
            self.store.authorize(denied.approval_id, self.request)

    def test_exact_approved_request_can_be_consumed_once(self) -> None:
        approval = self.store.create(self.request)
        self.store.decide(approval.approval_id, "approved")

        consumed = self.store.authorize(approval.approval_id, self.request)
        self.assertEqual(consumed.status, "consumed")
        with self.assertRaisesRegex(ApprovalError, "already consumed"):
            self.store.authorize(approval.approval_id, self.request)

    def test_modified_request_is_rejected_without_consuming_approval(self) -> None:
        approval = self.store.create(self.request)
        self.store.decide(approval.approval_id, "approved")
        modified = type(self.request)(
            name=self.request.name,
            arguments=self.request.arguments,
            fingerprint="0" * 64,
        )

        with self.assertRaisesRegex(ApprovalError, "does not match"):
            self.store.authorize(approval.approval_id, modified)
        self.assertEqual(self.store.get(approval.approval_id).status, "approved")

    def test_expired_request_is_rejected_and_persisted_as_expired(self) -> None:
        approval = self.store.create(self.request)
        self.store.decide(approval.approval_id, "approved")
        self.clock.value += timedelta(minutes=11)

        with self.assertRaisesRegex(ApprovalError, "has expired"):
            self.store.authorize(approval.approval_id, self.request)
        self.assertEqual(self.store.get(approval.approval_id).status, "expired")
        with self.assertRaisesRegex(ApprovalError, "has expired"):
            self.store.authorize(approval.approval_id, self.request)


if __name__ == "__main__":
    unittest.main()
