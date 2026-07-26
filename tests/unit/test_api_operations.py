from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from services.api.operations import (
    health_response,
    latest_predictions_response,
    latest_rul_predictions_response,
    list_assets_response,
    predictions_by_asset_response,
    predictions_by_run_response,
    rul_prediction_by_asset_response,
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
        "prediction_type": "risk_baseline",
        "model_name": "sentinelops-risk-baseline",
        "model_version": "1.0.0",
        "scored_at": scored_at,
        "source_feature_path": f"data/processed/features_{run_id}.csv",
        "source_feature_sha256": "a" * 64,
        "model_artifact_sha256": "",
        "dataset_id": "",
        "feature_contract_version": "",
        "remaining_useful_life_cycles": "",
        "risk_score": "0.5000",
        "health_score": "0.5000",
        "asset_status": "warning",
        "maintenance_priority": "high",
        "recommended_action": "Schedule maintenance within 24 hours.",
    }


def rul_prediction_row(
    *,
    asset_id: str = "FD001-ENGINE-005",
    run_id: str = "rul-run",
    scored_at: str = "2026-07-26T14:00:00Z",
    rul: str = "12.50",
) -> dict[str, str]:
    return {
        "run_id": run_id,
        "asset_id": asset_id,
        "prediction_type": "rul",
        "model_name": "sentinelops-rul-random-forest",
        "model_version": "1.0.0",
        "scored_at": scored_at,
        "source_feature_path": "data/processed/cmapss-fd001/validation.csv",
        "source_feature_sha256": "b" * 64,
        "model_artifact_sha256": "c" * 64,
        "dataset_id": "NASA-CMAPSS-FD001",
        "feature_contract_version": "1.0.0",
        "remaining_useful_life_cycles": rul,
        "risk_score": "0.9000",
        "health_score": "0.1000",
        "asset_status": "critical",
        "maintenance_priority": "immediate",
        "recommended_action": "Inspect asset and schedule immediate maintenance.",
    }


class ApiOperationTests(unittest.TestCase):
    def test_health_response_returns_service_status(self):
        response = health_response()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["status"], "ok")
        self.assertEqual(response.body["request_state"], "ok")
        self.assertEqual(response.body["message"], "api service is healthy")
        self.assertTrue(response.body["data"]["healthy"])

    def test_list_assets_response_returns_configured_asset_profiles(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            asset_path = project_root / "data" / "samples" / "asset_profiles.csv"
            asset_path.parent.mkdir(parents=True)
            asset_path.write_text(ASSET_CONFIG, encoding="utf-8")

            response = list_assets_response(project_root)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["message"], "asset profiles retrieved")
        self.assertEqual(
            [asset["asset_id"] for asset in response.body["data"]["assets"]],
            ["TEST-1", "TEST-2"],
        )

    def test_list_assets_response_returns_unavailable_when_source_is_missing(self):
        with TemporaryDirectory() as temp_dir:
            response = list_assets_response(Path(temp_dir))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.body["status"], "unavailable")
        self.assertEqual(response.body["request_state"], "unavailable")
        self.assertIn("asset profile source is unavailable", response.body["message"])

    def test_list_assets_response_returns_error_for_invalid_source(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            asset_path = project_root / "data" / "samples" / "asset_profiles.csv"
            asset_path.parent.mkdir(parents=True)
            asset_path.write_text("asset_id\nTEST-1\n", encoding="utf-8")

            response = list_assets_response(project_root)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.body["status"], "error")
        self.assertEqual(response.body["request_state"], "error")
        self.assertIn("missing fields", response.body["message"])

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
        self.assertEqual(response.body["request_state"], "not_found")
        self.assertIn("workflow run not found", response.body["message"])

    def test_workflow_status_response_returns_validation_error(self):
        with TemporaryDirectory() as temp_dir:
            response = workflow_status_response(Path(temp_dir), "../bad")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.body["status"], "error")
        self.assertEqual(response.body["request_state"], "error")
        self.assertIn("file-safe", response.body["message"])

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
        self.assertEqual(
            summary_response.body["message"],
            "workflow summary retrieved",
        )

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

    def test_latest_predictions_response_returns_one_row_per_asset(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            repository = CsvPredictionRepository(project_root / "data" / "predictions")
            repository.save([prediction_row(scored_at="2026-06-26T10:00:00Z")])
            repository.save(
                [
                    prediction_row(
                        asset_id="TEST-1",
                        run_id="run-2",
                        scored_at="2026-06-26T11:00:00Z",
                    ),
                    prediction_row(
                        asset_id="TEST-2",
                        run_id="run-2",
                        scored_at="2026-06-26T11:00:00Z",
                    ),
                ]
            )

            response = latest_predictions_response(project_root)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [row["asset_id"] for row in response.body["data"]["predictions"]],
            ["TEST-1", "TEST-2"],
        )
        self.assertEqual(
            response.body["data"]["predictions"][0]["run_id"],
            "run-2",
        )

    def test_rul_responses_only_return_compatible_predictions(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            repository = CsvPredictionRepository(
                project_root / "data" / "predictions"
            )
            repository.save([prediction_row()])
            repository.save([rul_prediction_row()])
            repository.save(
                [
                    prediction_row(
                        asset_id="FD001-ENGINE-005",
                        run_id="newer-baseline-run",
                        scored_at="2026-07-26T15:00:00Z",
                    )
                ]
            )

            latest_response = latest_rul_predictions_response(project_root)
            asset_response = rul_prediction_by_asset_response(
                project_root,
                "FD001-ENGINE-005",
            )
            baseline_asset_response = rul_prediction_by_asset_response(
                project_root,
                "TEST-1",
            )

        self.assertEqual(latest_response.status_code, 200)
        self.assertEqual(asset_response.status_code, 200)
        self.assertEqual(baseline_asset_response.status_code, 404)
        self.assertEqual(
            latest_response.body["data"]["predictions"][0]["prediction_type"],
            "rul",
        )
        self.assertEqual(
            latest_response.body["data"]["predictions"][0]["run_id"],
            "rul-run",
        )
        self.assertEqual(
            asset_response.body["data"]["predictions"][0][
                "remaining_useful_life_cycles"
            ],
            "12.50",
        )

    def test_prediction_responses_return_not_found_when_data_is_missing(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            run_response = predictions_by_run_response(project_root, "missing")
            asset_response = predictions_by_asset_response(project_root, "A-404")

        self.assertEqual(run_response.status_code, 404)
        self.assertEqual(asset_response.status_code, 404)
        self.assertEqual(run_response.body["request_state"], "not_found")
        self.assertEqual(asset_response.body["request_state"], "not_found")

    def test_prediction_response_returns_error_for_invalid_identifier(self):
        with TemporaryDirectory() as temp_dir:
            response = predictions_by_run_response(Path(temp_dir), "../bad")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.body["status"], "error")
        self.assertEqual(response.body["request_state"], "error")
        self.assertIn("file-safe", response.body["message"])


if __name__ == "__main__":
    unittest.main()
