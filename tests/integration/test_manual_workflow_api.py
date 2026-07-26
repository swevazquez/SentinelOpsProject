from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from services.api.app import create_app
from tests.rul_test_support import prepare_rul_runtime


class ManualWorkflowApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temporary_directory.name)
        sample_dir = self.project_root / "data" / "samples"
        sample_dir.mkdir(parents=True)
        self.asset_path = sample_dir / "asset_profiles.csv"
        self.asset_path.write_text(
            "asset_id,base_temperature_c,base_vibration_mm_s,"
            "base_pressure_kpa,runtime_hours,failure_risk\n"
            "PUMP-1,60,1.5,220,500,0.1\n",
            encoding="utf-8",
        )
        self.client = TestClient(create_app(self.project_root))

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _prepare_rul_runtime(self) -> None:
        prepare_rul_runtime(self.project_root)

    def test_supported_workflow_defaults_to_rul_and_runs_to_completion(self) -> None:
        self._prepare_rul_runtime()
        response = self.client.post(
            "/api/workflows", json={"workflow": "predictive-maintenance"}
        )

        self.assertEqual(response.status_code, 202)
        run_id = response.json()["data"]["workflow"]["run_id"]
        self.assertRegex(run_id, r"^manual-\d{8}T\d{6}Z-[0-9a-f]{8}$")
        status_response = self.client.get(f"/api/workflows/{run_id}")
        self.assertEqual(
            status_response.json()["data"]["workflow"]["status"], "completed"
        )
        prediction_path = (
            self.project_root / "data" / "predictions" / f"predictions_{run_id}.csv"
        )
        self.assertTrue(prediction_path.exists())
        predictions = self.client.get(
            f"/api/predictions/runs/{run_id}"
        ).json()["data"]["predictions"]
        self.assertEqual(
            {prediction["prediction_type"] for prediction in predictions},
            {"rul"},
        )
        self.assertEqual(response.json()["data"]["workflow"]["inference_mode"], "rul")

    def test_rul_workflow_persists_traceable_results_exposed_by_api(self) -> None:
        self._prepare_rul_runtime()

        response = self.client.post(
            "/api/workflows",
            json={
                "workflow": "predictive-maintenance",
                "inference_mode": "rul",
                "model_version": "1.0.0",
            },
        )

        self.assertEqual(response.status_code, 202)
        run_id = response.json()["data"]["workflow"]["run_id"]
        status_response = self.client.get(f"/api/workflows/{run_id}")
        predictions_response = self.client.get(
            f"/api/predictions/runs/{run_id}"
        )
        asset_response = self.client.get(
            "/api/predictions/assets/FD001-ENGINE-005"
        )

        self.assertEqual(
            status_response.json()["data"]["workflow"]["status"],
            "completed",
        )
        self.assertEqual(predictions_response.status_code, 200)
        self.assertEqual(asset_response.status_code, 200)
        predictions = predictions_response.json()["data"]["predictions"]
        self.assertEqual(len(predictions), 2)
        self.assertEqual(
            {prediction["run_id"] for prediction in predictions},
            {run_id},
        )
        self.assertEqual(
            {prediction["prediction_type"] for prediction in predictions},
            {"rul"},
        )
        self.assertTrue(
            all(prediction["remaining_useful_life_cycles"] for prediction in predictions)
        )
        self.assertTrue(all(prediction["model_version"] for prediction in predictions))
        self.assertTrue(all(prediction["dataset_id"] for prediction in predictions))
        self.assertTrue(
            all(prediction["feature_contract_version"] for prediction in predictions)
        )

    def test_missing_rul_artifact_fails_without_changing_existing_predictions(
        self,
    ) -> None:
        baseline_response = self.client.post(
            "/api/workflows",
            json={
                "workflow": "predictive-maintenance",
                "inference_mode": "baseline",
            },
        )
        baseline_run_id = baseline_response.json()["data"]["workflow"]["run_id"]
        baseline_path = (
            self.project_root
            / "data"
            / "predictions"
            / f"predictions_{baseline_run_id}.csv"
        )
        baseline_contents = baseline_path.read_text(encoding="utf-8")

        response = self.client.post(
            "/api/workflows",
            json={
                "workflow": "predictive-maintenance",
                "inference_mode": "rul",
            },
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn("trajectory does not exist", response.json()["detail"])
        self.assertEqual(
            baseline_path.read_text(encoding="utf-8"),
            baseline_contents,
        )
        self.assertEqual(
            len(
                list(
                    (self.project_root / "data" / "workflow-status").glob(
                        "workflow_*.json"
                    )
                )
            ),
            1,
        )

    def test_rul_demo_status_reset_and_completion_are_exposed(self) -> None:
        self._prepare_rul_runtime()

        initial = self.client.get("/api/workflows/rul-demo/status")
        reset = self.client.post("/api/workflows/rul-demo/reset")
        first_checkpoint_signature = None
        for checkpoint_number in range(1, 5):
            response = self.client.post(
                "/api/workflows",
                json={"workflow": "predictive-maintenance"},
            )
            self.assertEqual(response.status_code, 202)
            self.assertEqual(
                response.json()["data"]["workflow"]["demo_checkpoint"]["number"],
                checkpoint_number,
            )
            run_id = response.json()["data"]["workflow"]["run_id"]
            predictions = self.client.get(
                f"/api/predictions/runs/{run_id}"
            ).json()["data"]["predictions"]
            if checkpoint_number == 1:
                first_checkpoint_signature = {
                    prediction["asset_id"]: (
                        prediction["remaining_useful_life_cycles"],
                        prediction["risk_score"],
                        prediction["health_score"],
                        prediction["asset_status"],
                    )
                    for prediction in predictions
                }

        complete = self.client.get("/api/workflows/rul-demo/status")
        blocked = self.client.post(
            "/api/workflows",
            json={"workflow": "predictive-maintenance"},
        )
        replay_reset = self.client.post("/api/workflows/rul-demo/reset")
        replay = self.client.post(
            "/api/workflows",
            json={"workflow": "predictive-maintenance"},
        )
        replay_run_id = replay.json()["data"]["workflow"]["run_id"]
        replay_predictions = self.client.get(
            f"/api/predictions/runs/{replay_run_id}"
        ).json()["data"]["predictions"]
        replay_signature = {
            prediction["asset_id"]: (
                prediction["remaining_useful_life_cycles"],
                prediction["risk_score"],
                prediction["health_score"],
                prediction["asset_status"],
            )
            for prediction in replay_predictions
        }

        self.assertEqual(initial.status_code, 200)
        self.assertEqual(initial.json()["data"]["scenario"]["status"], "ready")
        self.assertEqual(reset.status_code, 200)
        self.assertTrue(reset.json()["data"]["scenario"]["history_retained"])
        self.assertEqual(
            complete.json()["data"]["scenario"]["completed_checkpoints"],
            4,
        )
        self.assertEqual(complete.json()["data"]["scenario"]["status"], "complete")
        self.assertEqual(blocked.status_code, 409)
        self.assertIn("reset", blocked.json()["detail"])
        self.assertEqual(replay_reset.status_code, 200)
        self.assertEqual(first_checkpoint_signature, replay_signature)
        self.assertEqual(
            len(list((self.project_root / "data" / "raw" / "rul-demo").glob("*.csv"))),
            5,
        )
        self.assertEqual(
            len(list((self.project_root / "data" / "predictions").glob("*.csv"))),
            5,
        )

    def test_explicit_baseline_mode_remains_available_for_local_testing(self) -> None:
        response = self.client.post(
            "/api/workflows",
            json={
                "workflow": "predictive-maintenance",
                "inference_mode": "baseline",
            },
        )

        self.assertEqual(response.status_code, 202)
        workflow = response.json()["data"]["workflow"]
        self.assertEqual(workflow["inference_mode"], "baseline")
        predictions = self.client.get(
            f"/api/predictions/runs/{workflow['run_id']}"
        ).json()["data"]["predictions"]
        self.assertEqual(
            {prediction["prediction_type"] for prediction in predictions},
            {"risk_baseline"},
        )

    def test_dashboard_read_endpoints_return_live_sources(self) -> None:
        assets_response = self.client.get("/api/assets")
        predictions_response = self.client.get("/api/predictions/latest")

        self.assertEqual(assets_response.status_code, 200)
        self.assertEqual(
            assets_response.json()["data"]["assets"][0]["asset_id"],
            "PUMP-1",
        )
        self.assertEqual(predictions_response.status_code, 200)
        self.assertEqual(predictions_response.json()["data"]["predictions"], [])

    def test_unsupported_workflow_does_not_create_status(self) -> None:
        response = self.client.post(
            "/api/workflows", json={"workflow": "unapproved-workflow"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse((self.project_root / "data" / "workflow-status").exists())

    def test_malformed_request_is_rejected(self) -> None:
        response = self.client.post(
            "/api/workflows",
            json={"workflow": "predictive-maintenance", "hours": 999},
        )
        self.assertEqual(response.status_code, 422)
        self.assertFalse((self.project_root / "data" / "workflow-status").exists())

    def test_execution_failure_is_recorded(self) -> None:
        self.asset_path.unlink()
        with self.assertRaises(FileNotFoundError):
            self.client.post(
                "/api/workflows",
                json={
                    "workflow": "predictive-maintenance",
                    "inference_mode": "baseline",
                },
            )

        status_files = list(
            (self.project_root / "data" / "workflow-status").glob("workflow_*.json")
        )
        self.assertEqual(len(status_files), 1)
        self.assertIn('"status": "failed"', status_files[0].read_text())


if __name__ == "__main__":
    unittest.main()
