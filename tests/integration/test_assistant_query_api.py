from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from services.api.app import create_app
from tests.fake_openai import FakeAssistantClient


class AssistantQueryApiTests(unittest.TestCase):
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
        self.assistant_client = FakeAssistantClient(
            tool_name="list_assets",
            answer="SentinelOps is monitoring one asset.",
        )
        self.client = TestClient(
            create_app(
                self.project_root,
                assistant_client=self.assistant_client,
            )
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_supported_query_returns_approved_tool_evidence(self) -> None:
        response = self.client.post(
            "/api/assistant/query",
            json={"message": "List monitored assets"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["request_state"], "completed")
        assistant_response = payload["data"]["response"]
        self.assertEqual(assistant_response["intent"], "list_assets")
        self.assertEqual(
            assistant_response["tool_calls"],
            [{"name": "list_assets", "read_only": True, "status_code": 200}],
        )
        self.assertEqual(assistant_response["provider"], "openai")

    def test_empty_and_unexpected_fields_are_rejected(self) -> None:
        empty_response = self.client.post(
            "/api/assistant/query",
            json={"message": "   "},
        )
        extra_response = self.client.post(
            "/api/assistant/query",
            json={"message": "List monitored assets", "tool": "run_workflow"},
        )

        self.assertEqual(empty_response.status_code, 400)
        self.assertEqual(extra_response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
