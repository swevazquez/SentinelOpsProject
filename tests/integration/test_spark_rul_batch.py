from __future__ import annotations

import csv
from datetime import UTC, datetime
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from services.api.operations import predictions_by_run_response
from services.ml.cmapss import RAW_FIELDS
from services.ml.prediction_store import prediction_repository
from services.persistence.postgres import postgres_connection
from services.spark_jobs.rul_batch import (
    SparkRulBatchConfig,
    create_local_spark_session,
    run_spark_rul_batch,
)
from services.workflows.status import get_workflow_status
from tests.rul_test_support import prepare_rul_runtime


TEST_DATABASE_URL = os.getenv("SENTINELOPS_TEST_DATABASE_URL")


class SparkRulBatchIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.spark = create_local_spark_session()
        cls.spark.sparkContext.setLogLevel("ERROR")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.spark.stop()

    def test_spark_batch_persists_traceable_rul_results_for_api_retrieval(self) -> None:
        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ,
            {"SENTINELOPS_PERSISTENCE_BACKEND": "file"},
            clear=False,
        ):
            project_root = Path(temp_dir)
            prepare_rul_runtime(project_root)
            input_path = Path("data/processed/cmapss-fd001/validation.csv")

            result = run_spark_rul_batch(
                SparkRulBatchConfig(
                    project_root=project_root,
                    input_path=input_path,
                    run_id="spark-success",
                    scored_at=datetime(2026, 8, 2, 16, 0, tzinfo=UTC),
                ),
                spark_session=self.spark,
            )
            stored = prediction_repository(project_root).get_by_run(
                "spark-success"
            )
            api_response = predictions_by_run_response(
                project_root,
                "spark-success",
            )
            workflow = get_workflow_status(project_root, "spark-success")

        self.assertEqual(result.input_row_count, 24)
        self.assertEqual(result.prediction_row_count, 2)
        self.assertEqual(result.asset_count, 2)
        self.assertEqual(api_response.status_code, 200)
        self.assertEqual(api_response.body["data"]["predictions"], stored)
        self.assertIsNotNone(workflow)
        assert workflow is not None
        self.assertEqual(workflow.status, "completed")
        self.assertEqual(
            [prediction["asset_id"] for prediction in stored],
            ["FD001-ENGINE-005", "FD001-ENGINE-006"],
        )
        for prediction in stored:
            self.assertEqual(prediction["run_id"], "spark-success")
            self.assertEqual(prediction["model_version"], "1.0.0")
            self.assertEqual(prediction["dataset_id"], "NASA-CMAPSS-FD001")
            self.assertEqual(prediction["feature_contract_version"], "1.0.0")
            self.assertEqual(
                prediction["source_feature_path"],
                input_path.as_posix(),
            )
            self.assertEqual(prediction["scored_at"], "2026-08-02T16:00:00Z")
            self.assertEqual(len(prediction["source_feature_sha256"]), 64)
            self.assertGreaterEqual(
                float(prediction["remaining_useful_life_cycles"]),
                0.0,
            )

    def test_malformed_spark_input_does_not_replace_last_valid_results(self) -> None:
        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ,
            {"SENTINELOPS_PERSISTENCE_BACKEND": "file"},
            clear=False,
        ):
            project_root = Path(temp_dir)
            prepare_rul_runtime(project_root)
            valid_path = Path("data/processed/cmapss-fd001/validation.csv")
            config = SparkRulBatchConfig(
                project_root=project_root,
                input_path=valid_path,
                run_id="spark-replacement",
            )
            run_spark_rul_batch(config, spark_session=self.spark)
            baseline = prediction_repository(project_root).get_by_run(
                config.run_id
            )
            malformed_path = project_root / "data" / "malformed.csv"
            with malformed_path.open("w", newline="", encoding="utf-8") as output:
                writer = csv.DictWriter(
                    output,
                    fieldnames=[field for field in RAW_FIELDS if field != "sensor_21"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        field: "1"
                        for field in RAW_FIELDS
                        if field != "sensor_21"
                    }
                )

            with self.assertRaisesRegex(ValueError, "missing required fields"):
                run_spark_rul_batch(
                    SparkRulBatchConfig(
                        project_root=project_root,
                        input_path=malformed_path,
                        run_id=config.run_id,
                    ),
                    spark_session=self.spark,
                )

            retained = prediction_repository(project_root).get_by_run(
                config.run_id
            )
            workflow = get_workflow_status(project_root, config.run_id)

        self.assertEqual(retained, baseline)
        self.assertIsNotNone(workflow)
        assert workflow is not None
        self.assertEqual(workflow.status, "failed")
        self.assertEqual(workflow.step, "spark_input_preparation")
        self.assertIn("ValueError", workflow.error or "")

    def test_missing_model_records_failed_inference_without_predictions(self) -> None:
        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ,
            {"SENTINELOPS_PERSISTENCE_BACKEND": "file"},
            clear=False,
        ):
            project_root = Path(temp_dir)
            prepare_rul_runtime(project_root)
            input_path = Path("data/processed/cmapss-fd001/validation.csv")

            with self.assertRaisesRegex(ValueError, "metadata does not exist"):
                run_spark_rul_batch(
                    SparkRulBatchConfig(
                        project_root=project_root,
                        input_path=input_path,
                        run_id="spark-missing-model",
                        model_version="9.9.9",
                    ),
                    spark_session=self.spark,
                )

            predictions = prediction_repository(project_root).get_by_run(
                "spark-missing-model"
            )
            workflow = get_workflow_status(project_root, "spark-missing-model")

        self.assertEqual(predictions, [])
        self.assertIsNotNone(workflow)
        assert workflow is not None
        self.assertEqual(workflow.status, "failed")
        self.assertEqual(workflow.step, "spark_rul_inference")

    @unittest.skipUnless(
        TEST_DATABASE_URL,
        "SENTINELOPS_TEST_DATABASE_URL is required for Spark/PostgreSQL testing",
    )
    def test_spark_batch_persists_results_through_postgres_boundary(self) -> None:
        run_id = "spark-postgres-contract"
        environment = {
            "SENTINELOPS_PERSISTENCE_BACKEND": "postgres",
            "DATABASE_URL": str(TEST_DATABASE_URL),
        }
        try:
            with TemporaryDirectory() as temp_dir, patch.dict(
                os.environ,
                environment,
                clear=False,
            ):
                project_root = Path(temp_dir)
                prepare_rul_runtime(project_root)

                result = run_spark_rul_batch(
                    SparkRulBatchConfig(
                        project_root=project_root,
                        input_path=Path(
                            "data/processed/cmapss-fd001/validation.csv"
                        ),
                        run_id=run_id,
                    ),
                    spark_session=self.spark,
                )
                api_response = predictions_by_run_response(project_root, run_id)
                workflow = get_workflow_status(project_root, run_id)
                prediction_dir_created = (
                    project_root / "data" / "predictions"
                ).exists()
                workflow_dir_created = (
                    project_root / "data" / "workflow-status"
                ).exists()

            self.assertEqual(result.prediction_row_count, 2)
            self.assertEqual(api_response.status_code, 200)
            self.assertIsNotNone(workflow)
            assert workflow is not None
            self.assertEqual(workflow.status, "completed")
            self.assertFalse(prediction_dir_created)
            self.assertFalse(workflow_dir_created)
        finally:
            if TEST_DATABASE_URL:
                with postgres_connection(str(TEST_DATABASE_URL)) as connection:
                    connection.execute(
                        "DELETE FROM sentinelops_predictions WHERE run_id = %s",
                        (run_id,),
                    )
                    connection.execute(
                        "DELETE FROM sentinelops_workflow_status WHERE run_id = %s",
                        (run_id,),
                    )


if __name__ == "__main__":
    unittest.main()
