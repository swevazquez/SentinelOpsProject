from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient

from services.api.app import create_app
from tests.fake_openai import FakeAssistantClient
from tests.rul_test_support import prepare_rul_runtime


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class RulExperienceAcceptanceTests(unittest.TestCase):
    def test_compatible_trajectory_reaches_api_assistant_and_ui_contract(
        self,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            prepare_rul_runtime(project_root)
            assistant_client = FakeAssistantClient(
                tool_name="get_rul_prediction_by_asset",
                arguments={"asset_id": "FD001-ENGINE-005"},
                answer=(
                    "FD001-ENGINE-005 has a stored RUL estimate with "
                    "immediate maintenance priority."
                ),
            )
            client = TestClient(
                create_app(
                    project_root,
                    assistant_client=assistant_client,
                )
            )

            workflow_response = client.post(
                "/api/workflows",
                json={
                    "workflow": "predictive-maintenance",
                },
            )
            run_id = workflow_response.json()["data"]["workflow"]["run_id"]
            run_response = client.get(f"/api/predictions/runs/{run_id}")
            latest_rul_response = client.get("/api/predictions/rul/latest")
            asset_rul_response = client.get(
                "/api/predictions/rul/assets/FD001-ENGINE-005"
            )
            assistant_response = client.post(
                "/api/assistant/query",
                json={"message": "What is the RUL for FD001-ENGINE-005?"},
            )

        self.assertEqual(workflow_response.status_code, 202)
        self.assertEqual(run_response.status_code, 200)
        self.assertEqual(latest_rul_response.status_code, 200)
        self.assertEqual(asset_rul_response.status_code, 200)
        self.assertEqual(assistant_response.status_code, 200)

        prediction = asset_rul_response.json()["data"]["predictions"][0]
        self.assertEqual(prediction["run_id"], run_id)
        self.assertEqual(prediction["prediction_type"], "rul")
        self.assertTrue(prediction["remaining_useful_life_cycles"])
        self.assertTrue(prediction["health_score"])
        self.assertTrue(prediction["maintenance_priority"])
        self.assertTrue(prediction["recommended_action"])
        self.assertEqual(prediction["model_version"], "1.0.0")
        self.assertTrue(prediction["scored_at"].endswith("Z"))

        assistant = assistant_response.json()["data"]["response"]
        self.assertEqual(assistant["intent"], "explain_asset_rul")
        self.assertEqual(
            assistant["items"][0]["remaining_useful_life_cycles"],
            prediction["remaining_useful_life_cycles"],
        )
        self.assertEqual(
            assistant["tool_calls"],
            [
                {
                    "name": "get_rul_prediction_by_asset",
                    "read_only": True,
                    "status_code": 200,
                }
            ],
        )

        dashboard_script = (
            PROJECT_ROOT / "frontend" / "dashboard" / "app.js"
        ).read_text(encoding="utf-8")
        dashboard_markup = (
            PROJECT_ROOT / "frontend" / "dashboard" / "index.html"
        ).read_text(encoding="utf-8")
        self.assertIn("remaining_useful_life_cycles", dashboard_script)
        self.assertIn(
            'optionalApiFetch("/api/predictions/rul/latest")',
            dashboard_script,
        )
        self.assertIn("asset.rul_available", dashboard_script)
        self.assertIn("RUL is unavailable", dashboard_script)
        self.assertIn("not a guaranteed failure date", dashboard_script)
        self.assertIn("<th>Risk Score</th><th>RUL</th>", dashboard_markup)
        self.assertIn("RUL: shortest horizon", dashboard_markup)


if __name__ == "__main__":
    unittest.main()
