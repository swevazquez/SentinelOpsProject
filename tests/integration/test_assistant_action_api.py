from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from services.api.app import create_app
from tests.fake_openai import FakeAssistantClient
from tests.rul_test_support import prepare_rul_runtime


class AssistantActionApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temporary_directory.name)
        sample_dir = self.project_root / "data" / "samples"
        sample_dir.mkdir(parents=True)
        (sample_dir / "asset_profiles.csv").write_text(
            "asset_id,base_temperature_c,base_vibration_mm_s,"
            "base_pressure_kpa,runtime_hours,failure_risk\n"
            "PUMP-1,60,1.5,220,500,0.1\n",
            encoding="utf-8",
        )
        prepare_rul_runtime(self.project_root)
        self.client = TestClient(
            create_app(
                self.project_root,
                assistant_client=FakeAssistantClient(
                    tool_name="start_workflow",
                    arguments={"workflow": "predictive-maintenance"},
                    answer="The workflow is ready for approval.",
                ),
            )
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _propose_action(self) -> dict[str, object]:
        response = self.client.post(
            "/api/assistant/query",
            json={"message": "Run predictive maintenance"},
        )
        self.assertEqual(response.status_code, 200)
        assistant_response = response.json()["data"]["response"]
        self.assertEqual(
            assistant_response["answer"],
            "I prepared the predictive-maintenance workflow action. "
            "Review the protected operation below before it runs.",
        )
        self.assertNotIn("approval_id", assistant_response["answer"])
        action = assistant_response["action_request"]
        self.assertEqual(action["status"], "pending")
        return action

    def _execute(self, action: dict[str, object]) -> object:
        return self.client.post(
            "/api/assistant/actions/execute",
            json={
                "approval_id": action["approval_id"],
                "action": action["action"],
                "arguments": action["arguments"],
            },
        )

    def test_assistant_action_requires_approval_without_starting_workflow(self) -> None:
        action = self._propose_action()

        self.assertEqual(action["action"], "start_workflow")
        self.assertTrue(action["requires_approval"])
        self.assertFalse((self.project_root / "data" / "workflow-status").exists())
        response = self._execute(action)
        self.assertEqual(response.status_code, 403)
        self.assertFalse((self.project_root / "data" / "workflow-status").exists())

    def test_denied_action_cannot_start_workflow(self) -> None:
        action = self._propose_action()
        decision = self.client.post(
            f"/api/assistant/approvals/{action['approval_id']}",
            json={"decision": "denied"},
        )

        self.assertEqual(decision.status_code, 200)
        self.assertEqual(self._execute(action).status_code, 403)
        self.assertFalse((self.project_root / "data" / "workflow-status").exists())

    def test_exact_approved_action_starts_once_and_preserves_traceability(self) -> None:
        action = self._propose_action()
        decision = self.client.post(
            f"/api/assistant/approvals/{action['approval_id']}",
            json={"decision": "approved"},
        )
        self.assertEqual(decision.status_code, 200)

        execution = self._execute(action)
        self.assertEqual(execution.status_code, 202)
        workflow = execution.json()["data"]["workflow"]
        status_response = self.client.get(f"/api/workflows/{workflow['run_id']}")
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()["data"]["workflow"]["status"], "completed")
        self.assertEqual(
            status_response.json()["data"]["workflow"]["approval_id"],
            action["approval_id"],
        )
        self.assertEqual(workflow["inference_mode"], "rul")
        self.assertEqual(workflow["demo_checkpoint"]["number"], 1)
        predictions = self.client.get(
            f"/api/predictions/runs/{workflow['run_id']}"
        ).json()["data"]["predictions"]
        self.assertEqual(
            {prediction["prediction_type"] for prediction in predictions},
            {"rul"},
        )

        replay = self._execute(action)
        self.assertEqual(replay.status_code, 409)
        status_files = list(
            (self.project_root / "data" / "workflow-status").glob("workflow_*.json")
        )
        self.assertEqual(len(status_files), 1)
        audit_events = [
            json.loads(line)
            for line in (
                self.project_root / "data" / "audit" / "agent-operations.jsonl"
            ).read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(
            [event["error_category"] for event in audit_events],
            ["approval_required", None, "approval_replayed"],
        )
        self.assertNotIn("arguments", str(audit_events))

    def test_modified_action_is_rejected_before_workflow_execution(self) -> None:
        action = self._propose_action()
        self.client.post(
            f"/api/assistant/approvals/{action['approval_id']}",
            json={"decision": "approved"},
        )
        modified = dict(action)
        modified["arguments"] = {"workflow": "unapproved-workflow"}

        response = self._execute(modified)
        self.assertEqual(response.status_code, 400)
        self.assertFalse((self.project_root / "data" / "workflow-status").exists())


if __name__ == "__main__":
    unittest.main()
