from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest
from unittest.mock import patch

from services.api.rul_demo import rul_demo_status
from services.ml.prediction_store import prediction_repository
from services.spark_jobs.rul_batch import create_local_spark_session
from services.workflows.airflow_pipeline import (
    execute_predictive_batch,
    finalize_predictive_workflow,
    select_predictive_input,
)
from services.workflows.status import get_workflow_status
from tests.rul_test_support import prepare_rul_runtime


class AirflowPipelineIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.spark = create_local_spark_session()
        cls.spark.sparkContext.setLogLevel("ERROR")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.spark.stop()

    def test_airflow_service_path_runs_spark_and_advances_demo_checkpoint(self):
        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ,
            {"SENTINELOPS_PERSISTENCE_BACKEND": "file"},
            clear=False,
        ):
            project_root = Path(temp_dir)
            prepare_rul_runtime(project_root)
            selection = select_predictive_input(
                project_root=project_root,
                run_id="airflow-success",
            )
            batch = execute_predictive_batch(
                project_root=project_root,
                selection=selection,
                spark_session=self.spark,
            )
            final = finalize_predictive_workflow(
                project_root=project_root,
                selection=selection,
                batch_result=batch,
            )
            predictions = prediction_repository(project_root).get_by_run(
                "airflow-success"
            )
            workflow = get_workflow_status(project_root, "airflow-success")
            scenario = rul_demo_status(project_root)

        self.assertEqual(batch["prediction_row_count"], 2)
        self.assertEqual(final["status"], "completed")
        self.assertEqual(len(predictions), 2)
        self.assertIsNotNone(workflow)
        assert workflow is not None
        self.assertEqual(workflow.status, "completed")
        self.assertEqual(workflow.step, "airflow_workflow_complete")
        self.assertEqual(scenario["completed_checkpoints"], 1)
        self.assertIsNone(scenario["active_run_id"])

    def test_spark_failure_releases_demo_checkpoint_and_preserves_no_predictions(self):
        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ,
            {"SENTINELOPS_PERSISTENCE_BACKEND": "file"},
            clear=False,
        ):
            project_root = Path(temp_dir)
            prepare_rul_runtime(project_root)
            selection = select_predictive_input(
                project_root=project_root,
                run_id="airflow-failure",
            )
            selection["input_path"] = "data/missing-input.csv"

            with self.assertRaisesRegex(ValueError, "does not exist"):
                execute_predictive_batch(
                    project_root=project_root,
                    selection=selection,
                    spark_session=self.spark,
                )

            predictions = prediction_repository(project_root).get_by_run(
                "airflow-failure"
            )
            workflow = get_workflow_status(project_root, "airflow-failure")
            scenario = rul_demo_status(project_root)

        self.assertEqual(predictions, [])
        self.assertIsNotNone(workflow)
        assert workflow is not None
        self.assertEqual(workflow.status, "failed")
        self.assertEqual(workflow.step, "spark_input_preparation")
        self.assertIsNone(scenario["active_run_id"])


if __name__ == "__main__":
    unittest.main()
