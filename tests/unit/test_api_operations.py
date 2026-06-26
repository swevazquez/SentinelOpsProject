from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from services.api.operations import (
    health_response,
    list_assets_response,
    predictions_by_asset_response,
    predictions_by_run_response,
    workflow_list_response,
    workflow_status_response,
    workflow_summary_response,
)
from services.ml.prediction_store import CsvPredictionRepository
from services.workflows.status import record_workflow_status


ASSET_CONFIG = "\n".join(
    [
        "asset_id,base_temperature_c,base_vibration_mm_s,base_pressure_kpa,runtime_hours,failure_risk",
        "TEST-1,70.0,2.5,220.0,100,0.1",
        "TEST-2,84.0,5.5,248.0,2600,0.6",
    ]
)


def prediction_row(
    *,
    asset_id: str = "TEST-1",
    run_id: str = "run-1",
    scored_at: str = "2026-06-26T10:00:00Z",
) -> dict[str, str]:
    return {
        "run_id": run_id,
        "asset_id": asset_id,
        "model_name": "sentinelops-risk-baseline",
        "model_version": "1.0.0",
        "scored_at": scored_at,
        "source_feature_path": f"data/processed/features_{run_id}.csv",
        "source_feature_sha256": "a" * 64,
        "risk_score": "0.5000",
        "asset_status": "warning",
        "maintenance_priority": "high",
        "recommended_action": "Schedule maintenance within 24 hours.",
    }


class ApiOperationTests(unittest.TestCase):
    def test_health_response_returns_service_status(self):
        response = health_response()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["status"], "ok")
        self.assertTrue(response.body["data"]["healthy"])

    def test_list_assets_response_returns_configured_asset_profiles(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            asset_path = project_root / "data" / "samples" / "asset_profiles.csv"
            asset_path.parent.mkdir(parents=True)
            asset_path.write_text(ASSET_CONFIG, encoding="utf-8")

            response = list_assets_response(project_root)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [asset["asset_id"] for asset in response.body["data"]["assets"]],
            ["TEST-1", "TEST-2"],
        )

    def test_workflow_status_response_returns_completed_run(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            record_workflow_status(
                project_root=project_root,
                run_id="completed-run",
                status="completed",
            )

            response = workflow_status_response(project_root, "completed-run")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.body["data"]["workflow"]["status"],
            "completed",
        )

    def test_workflow_status_response_returns_not_found_for_missing_run(self):
        with TemporaryDirectory() as temp_dir:
            response = workflow_status_response(Path(temp_dir), "missing")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.body["status"], "not_found")

    def test_workflow_status_response_returns_validation_error(self):
        with TemporaryDirectory() as temp_dir:
            response = workflow_status_response(Path(temp_dir), "../bad")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.body["status"], "error")

    def test_workflow_list_and_summary_responses_return_operational_status(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            record_workflow_status(
                project_root=project_root,
                run_id="running-run",
                status="running",
            )
            record_workflow_status(
                project_root=project_root,
                run_id="failed-run",
                status="failed",
                step="engineer_and_persist_features",
                error="failed",
            )

            list_response = workflow_list_response(project_root)
            summary_response = workflow_summary_response(project_root)

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.body["data"]["workflows"]), 2)
        self.assertEqual(summary_response.status_code, 200)
        self.assertEqual(summary_response.body["data"]["summary"]["total"], 2)
        self.assertEqual(summary_response.body["data"]["summary"]["running"], 1)
        self.assertEqual(summary_response.body["data"]["summary"]["failed"], 1)

    def test_predictions_by_run_response_returns_stored_predictions(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            CsvPredictionRepository(
                project_root / "data" / "predictions"
            ).save([prediction_row()])

            response = predictions_by_run_response(project_root, "run-1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.body["data"]["predictions"][0]["asset_id"],
            "TEST-1",
        )

    def test_predictions_by_asset_response_returns_stored_predictions(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            CsvPredictionRepository(
                project_root / "data" / "predictions"
            ).save([prediction_row(asset_id="TEST-2")])

            response = predictions_by_asset_response(project_root, "TEST-2")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.body["data"]["predictions"][0]["asset_id"],
            "TEST-2",
        )

    def test_prediction_responses_return_not_found_when_data_is_missing(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            run_response = predictions_by_run_response(project_root, "missing")
            asset_response = predictions_by_asset_response(project_root, "A-404")

        self.assertEqual(run_response.status_code, 404)
        self.assertEqual(asset_response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
