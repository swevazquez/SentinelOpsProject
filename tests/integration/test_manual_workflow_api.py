from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from services.api.app import create_app


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

    def test_supported_workflow_runs_to_completion(self) -> None:
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
                "/api/workflows", json={"workflow": "predictive-maintenance"}
            )

        status_files = list(
            (self.project_root / "data" / "workflow-status").glob("workflow_*.json")
        )
        self.assertEqual(len(status_files), 1)
        self.assertIn('"status": "failed"', status_files[0].read_text())


if __name__ == "__main__":
    unittest.main()
