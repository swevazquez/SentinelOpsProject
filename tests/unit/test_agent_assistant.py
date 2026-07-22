from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from services.agent.assistant import SYSTEM_INSTRUCTIONS, answer_operational_query
from services.ml.prediction_store import CsvPredictionRepository
from services.ml.scoring import score_feature_rows
from services.workflows.status import record_workflow_status
from tests.fake_openai import FakeAssistantClient


class AgentAssistantTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temporary_directory.name)
        sample_dir = self.project_root / "data" / "samples"
        sample_dir.mkdir(parents=True)
        with (sample_dir / "asset_profiles.csv").open("w", newline="") as output:
            writer = csv.writer(output)
            writer.writerow(
                [
                    "asset_id",
                    "base_temperature_c",
                    "base_vibration_mm_s",
                    "base_pressure_kpa",
                    "runtime_hours",
                    "failure_risk",
                ]
            )
            writer.writerow(["PUMP-1", "60", "1.5", "220", "500", "0.1"])
        record_workflow_status(
            project_root=self.project_root,
            run_id="run-completed",
            status="completed",
        )
        record_workflow_status(
            project_root=self.project_root,
            run_id="run-failed",
            status="failed",
            step="score_and_persist_predictions",
            error="scoring failed",
        )
        predictions = score_feature_rows(
            [
                {
                    "run_id": "run-completed",
                    "asset_id": "PUMP-1",
                    "max_temperature_c": "90",
                    "max_vibration_mm_s": "8.5",
                    "avg_pressure_kpa": "180",
                    "max_runtime_hours": "9500",
                    "failure_observed": "1",
                }
            ]
        )
        CsvPredictionRepository(self.project_root / "data" / "predictions").save(
            predictions
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_highest_risk_query_uses_latest_prediction_tool(self) -> None:
        client = FakeAssistantClient(
            tool_name="get_latest_predictions",
            answer="PUMP-1 has the highest current risk.",
        )
        response = answer_operational_query(
            self.project_root,
            "Show highest risk assets",
            client=client,
            model="test-model",
        )

        self.assertEqual(response["intent"], "highest_risk_assets")
        self.assertEqual(response["items"][0]["asset_id"], "PUMP-1")
        self.assertNotIn("source_feature_path", response["items"][0])
        self.assertNotIn("source_feature_sha256", response["items"][0])
        self.assertEqual(
            response["tool_calls"],
            [
                {
                    "name": "get_latest_predictions",
                    "read_only": True,
                    "status_code": 200,
                }
            ],
        )
        self.assertEqual(response["provider"], "openai")
        self.assertEqual(response["model"], "test-model")
        self.assertTrue(response["correlation_id"])
        audit_path = self.project_root / "data" / "audit" / "agent-operations.jsonl"
        audit_event = json.loads(audit_path.read_text(encoding="utf-8"))
        self.assertEqual(audit_event["correlation_id"], response["correlation_id"])
        self.assertEqual(audit_event["operation_name"], "get_latest_predictions")
        self.assertEqual(audit_event["outcome"], "succeeded")
        self.assertNotIn("source_feature_path", str(client.requests[1]["input"]))
        self.assertIn("plain text without Markdown", SYSTEM_INSTRUCTIONS)

    def test_asset_prediction_query_returns_grounded_explanation(self) -> None:
        client = FakeAssistantClient(
            tool_name="get_predictions_by_asset",
            arguments={"asset_id": "PUMP-1"},
            answer="PUMP-1 is critical. Recommended action: inspect the asset.",
        )
        response = answer_operational_query(
            self.project_root,
            "Explain the prediction for PUMP-1",
            client=client,
        )

        self.assertEqual(response["intent"], "explain_asset_prediction")
        self.assertIn("PUMP-1", response["answer"])
        self.assertIn("Recommended action", response["answer"])
        self.assertEqual(response["tool_calls"][0]["name"], "get_predictions_by_asset")

    def test_workflow_failure_query_returns_failed_runs_only(self) -> None:
        client = FakeAssistantClient(
            tool_name="list_workflows",
            answer="There is one failed workflow run.",
        )
        response = answer_operational_query(
            self.project_root,
            "Summarize workflow failures",
            client=client,
        )

        self.assertEqual(response["intent"], "workflow_failures")
        self.assertEqual([item["run_id"] for item in response["items"]], ["run-failed"])
        self.assertEqual(response["tool_calls"][0]["name"], "list_workflows")

    def test_unsupported_query_does_not_execute_a_tool(self) -> None:
        client = FakeAssistantClient(
            tool_name=None,
            answer="I can only answer SentinelOps operational questions.",
        )
        response = answer_operational_query(
            self.project_root,
            "What is the weather?",
            client=client,
        )

        self.assertEqual(response["intent"], "operational_query")
        self.assertEqual(response["tool_calls"], [])
        self.assertEqual(len(client.requests), 1)

    def test_invalid_model_tool_arguments_are_audited_before_rejection(self) -> None:
        class InvalidArgumentsClient:
            def create_response(self, **kwargs: object) -> object:
                return SimpleNamespace(
                    output=[
                        SimpleNamespace(
                            type="function_call",
                            name="get_workflow",
                            arguments="not-json",
                            call_id="call-invalid",
                        )
                    ],
                    output_text="",
                )

        with self.assertRaisesRegex(ValueError, "invalid tool arguments"):
            answer_operational_query(
                self.project_root,
                "Show workflow status",
                client=InvalidArgumentsClient(),
            )

        audit_path = self.project_root / "data" / "audit" / "agent-operations.jsonl"
        event = json.loads(audit_path.read_text(encoding="utf-8"))
        self.assertEqual(event["operation_name"], "get_workflow")
        self.assertEqual(event["outcome"], "rejected")
        self.assertEqual(event["error_category"], "validation_error")
        self.assertNotIn("not-json", audit_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
