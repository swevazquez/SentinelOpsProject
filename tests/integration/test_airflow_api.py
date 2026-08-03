from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from services.api.app import create_app


class AirflowWorkflowApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temporary_directory.name)
        (self.project_root / "data").mkdir()
        self.client = TestClient(
            create_app(self.project_root),
            raise_server_exceptions=False,
        )
        self.environment = patch.dict(
            os.environ,
            {
                "SENTINELOPS_WORKFLOW_BACKEND": "airflow",
                "AIRFLOW_API_URL": "http://airflow:8080/api/v1",
                "AIRFLOW_API_USERNAME": "airflow",
                "AIRFLOW_API_PASSWORD": "secret",
            },
        )
        self.environment.start()

    def tearDown(self) -> None:
        self.environment.stop()
        self.temporary_directory.cleanup()

    @patch("services.api.app.trigger_dag_run")
    def test_dashboard_workflow_is_submitted_to_airflow(self, trigger) -> None:
        def submit(*, run_id: str, model_version: str, settings: object) -> dict[str, object]:
            return {"dag_run_id": run_id, "state": "queued"}

        trigger.side_effect = submit

        response = self.client.post(
            "/api/workflows",
            json={"workflow": "predictive-maintenance"},
        )

        self.assertEqual(response.status_code, 202)
        workflow = response.json()["data"]["workflow"]
        self.assertEqual(workflow["orchestrator"], "airflow")
        self.assertEqual(workflow["dag_id"], "sentinelops_predictive_maintenance")
        self.assertEqual(workflow["airflow_run_id"], workflow["run_id"])
        self.assertEqual(workflow["demo_checkpoint"], None)
        trigger.assert_called_once()
        status = self.client.get(f"/api/workflows/{workflow['run_id']}")
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()["data"]["workflow"]["status"], "running")

    @patch("services.api.app.trigger_dag_run")
    def test_airflow_failure_is_recorded_and_reported(self, trigger) -> None:
        trigger.side_effect = RuntimeError("Airflow trigger failed")

        response = self.client.post(
            "/api/workflows",
            json={"workflow": "predictive-maintenance"},
        )

        self.assertEqual(response.status_code, 500)
        status_files = list(
            (self.project_root / "data" / "workflow-status").glob("*.json")
        )
        self.assertEqual(len(status_files), 1)
        self.assertIn('"status": "failed"', status_files[0].read_text())


if __name__ == "__main__":
    unittest.main()
