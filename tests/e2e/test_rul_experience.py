from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient

from services.api.app import create_app
from services.ml.rul_training import TrainingConfig, train_rul_model
from tests.fake_openai import FakeAssistantClient
from tests.unit.test_rul_training import write_metadata, write_partition


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class RulExperienceAcceptanceTests(unittest.TestCase):
    def test_compatible_trajectory_reaches_api_assistant_and_ui_contract(
        self,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            processed_dir = (
                project_root / "data" / "processed" / "cmapss-fd001"
            )
            processed_dir.mkdir(parents=True)
            training_ids = (1, 2, 3, 4)
            validation_ids = (5, 6)
            training_path = processed_dir / "training.csv"
            validation_path = processed_dir / "validation.csv"
            metadata_path = processed_dir / "metadata.json"
            write_partition(training_path, training_ids)
            write_partition(validation_path, validation_ids)
            write_metadata(metadata_path, training_ids, validation_ids)
            train_rul_model(
                training_path,
                validation_path,
                metadata_path,
                project_root / "data" / "models" / "rul-random-forest",
                config=TrainingConfig(
                    model_version="1.0.0",
                    rolling_window=3,
                    n_estimators=8,
                    max_depth=5,
                ),
            )
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
                    "inference_mode": "rul",
                    "model_version": "1.0.0",
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
