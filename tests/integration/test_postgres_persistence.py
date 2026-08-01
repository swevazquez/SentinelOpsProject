from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from services.api.app import create_app
from services.ml.prediction_store import prediction_repository
from services.persistence.postgres import postgres_connection
from services.workflows.status import record_workflow_status


TEST_DATABASE_URL = os.getenv("SENTINELOPS_TEST_DATABASE_URL")


def rul_prediction(run_id: str, asset_id: str, scored_at: str) -> dict[str, str]:
    return {
        "run_id": run_id,
        "asset_id": asset_id,
        "prediction_type": "rul",
        "model_name": "sentinelops-rul-random-forest",
        "model_version": "1.0.0",
        "scored_at": scored_at,
        "source_feature_path": f"data/processed/{run_id}.csv",
        "source_feature_sha256": "a" * 64,
        "model_artifact_sha256": "b" * 64,
        "dataset_id": "cmapps-fd001",
        "feature_contract_version": "1.0.0",
        "remaining_useful_life_cycles": "42.5000",
        "risk_score": "0.5750",
        "health_score": "0.4250",
        "asset_status": "warning",
        "maintenance_priority": "high",
        "recommended_action": "Schedule maintenance planning.",
    }


@unittest.skipUnless(
    TEST_DATABASE_URL,
    "SENTINELOPS_TEST_DATABASE_URL is required for PostgreSQL integration tests",
)
class PostgresPersistenceIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database_url = str(TEST_DATABASE_URL)
        suffix = uuid4().hex[:10]
        self.run_id = f"postgres-{suffix}"
        self.approval_id = f"approval-{suffix}"
        self.asset_ids = [f"ENGINE-{suffix}-1", f"ENGINE-{suffix}-2"]
        self.environment = {
            "SENTINELOPS_PERSISTENCE_BACKEND": "postgres",
            "DATABASE_URL": self.database_url,
        }

    def tearDown(self) -> None:
        if not TEST_DATABASE_URL:
            return
        with postgres_connection(self.database_url) as connection:
            connection.execute(
                "DELETE FROM sentinelops_predictions WHERE run_id = %s",
                (self.run_id,),
            )
            connection.execute(
                "DELETE FROM sentinelops_workflow_status WHERE run_id = %s",
                (self.run_id,),
            )

    def test_predictions_and_workflow_state_survive_api_recreation(self) -> None:
        rows = [
            rul_prediction(
                self.run_id,
                self.asset_ids[0],
                "2026-08-01T14:00:00Z",
            ),
            rul_prediction(
                self.run_id,
                self.asset_ids[1],
                "2026-08-01T14:00:01Z",
            ),
        ]
        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ, self.environment, clear=False
        ):
            project_root = Path(temp_dir)
            record_workflow_status(
                project_root=project_root,
                run_id=self.run_id,
                status="running",
                step="rul_inference_and_persistence",
                approval_id=self.approval_id,
            )
            storage_result = prediction_repository(project_root).save(rows)
            record_workflow_status(
                project_root=project_root,
                run_id=self.run_id,
                status="completed",
            )

            with TestClient(create_app(project_root)) as first_client:
                first_predictions = first_client.get(
                    f"/api/predictions/runs/{self.run_id}"
                )
                first_workflow = first_client.get(
                    f"/api/workflows/{self.run_id}"
                )

            with TestClient(create_app(project_root)) as restarted_client:
                restarted_predictions = restarted_client.get(
                    f"/api/predictions/runs/{self.run_id}"
                )
                restarted_workflow = restarted_client.get(
                    f"/api/workflows/{self.run_id}"
                )

        self.assertIsNone(storage_result.path)
        self.assertEqual(storage_result.row_count, 2)
        self.assertEqual(first_predictions.status_code, 200)
        self.assertEqual(first_workflow.status_code, 200)
        self.assertEqual(restarted_predictions.status_code, 200)
        self.assertEqual(restarted_workflow.status_code, 200)
        self.assertEqual(restarted_predictions.json(), first_predictions.json())
        self.assertEqual(restarted_workflow.json(), first_workflow.json())
        stored_rows = restarted_predictions.json()["data"]["predictions"]
        self.assertEqual(stored_rows, rows)
        self.assertEqual(
            restarted_workflow.json()["data"]["workflow"]["status"],
            "completed",
        )
        self.assertEqual(
            restarted_workflow.json()["data"]["workflow"]["approval_id"],
            self.approval_id,
        )
        self.assertFalse((project_root / "data" / "predictions").exists())
        self.assertFalse((project_root / "data" / "workflow-status").exists())

    def test_prediction_repository_satisfies_query_contract(self) -> None:
        rows = [
            rul_prediction(
                self.run_id,
                self.asset_ids[0],
                "2026-08-01T14:00:00Z",
            ),
            rul_prediction(
                self.run_id,
                self.asset_ids[1],
                "2026-08-01T14:00:01Z",
            ),
        ]
        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ, self.environment, clear=False
        ):
            repository = prediction_repository(Path(temp_dir))
            repository.save(rows)

            by_run = repository.get_by_run(self.run_id)
            by_asset = repository.get_by_asset(self.asset_ids[0])
            latest = repository.get_latest()
            latest_rul = repository.get_latest_by_type("rul")

        self.assertEqual(by_run, rows)
        self.assertEqual(by_asset, [rows[0]])
        self.assertEqual(latest, rows)
        self.assertEqual(latest_rul, rows)

    def test_failed_replacement_keeps_last_committed_prediction_set(self) -> None:
        original_rows = [
            rul_prediction(
                self.run_id,
                self.asset_ids[0],
                "2026-08-01T14:00:00Z",
            )
        ]
        replacement_rows = [
            {
                **original_rows[0],
                "remaining_useful_life_cycles": "20.0000",
                "scored_at": "2026-08-01T15:00:00Z",
            }
        ]
        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ, self.environment, clear=False
        ):
            repository = prediction_repository(Path(temp_dir))
            repository.save(original_rows)

            with patch(
                "services.ml.prediction_store.Jsonb",
                side_effect=RuntimeError("simulated write interruption"),
            ):
                with self.assertRaisesRegex(RuntimeError, "write interruption"):
                    repository.save(replacement_rows)

            stored_rows = repository.get_by_run(self.run_id)

        self.assertEqual(stored_rows, original_rows)


if __name__ == "__main__":
    unittest.main()
