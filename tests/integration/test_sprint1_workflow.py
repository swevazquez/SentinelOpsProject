from __future__ import annotations

import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from services.simulator.telemetry import RawTelemetryStorageResult
from services.spark_jobs.features import FeatureStorageResult
from services.workflows.sprint1 import run_sprint1_workflow


ASSET_CONFIG = "\n".join(
    [
        "asset_id,base_temperature_c,base_vibration_mm_s,base_pressure_kpa,runtime_hours,failure_risk",
        "TEST-1,70.0,2.5,220.0,100,0.1",
        "TEST-2,80.0,4.0,235.0,200,0.4",
    ]
)


class Sprint1WorkflowTests(unittest.TestCase):
    def test_workflow_persists_raw_and_feature_artifacts_for_one_run(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            config_path = project_root / "data" / "samples" / "asset_profiles.csv"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(ASSET_CONFIG, encoding="utf-8")

            result = run_sprint1_workflow(
                project_root=project_root,
                run_id="integration-run",
                hours=3,
                seed=7,
            )

            self.assertEqual(result.run_id, "integration-run")
            self.assertEqual(result.raw_row_count, 6)
            self.assertEqual(result.feature_row_count, 2)
            self.assertEqual(
                result.raw_path,
                project_root / "data" / "raw" / "telemetry_integration-run.csv",
            )
            self.assertEqual(
                result.feature_path,
                project_root
                / "data"
                / "processed"
                / "features_integration-run.csv",
            )
            self.assertTrue(result.raw_path.exists())
            self.assertTrue(result.feature_path.exists())

            status_path = (
                project_root
                / "data"
                / "workflow-status"
                / "workflow_integration-run.json"
            )
            status_record = json.loads(status_path.read_text(encoding="utf-8"))

            with result.feature_path.open(newline="", encoding="utf-8") as feature_file:
                feature_rows = list(csv.DictReader(feature_file))

        self.assertEqual(status_record["run_id"], "integration-run")
        self.assertEqual(status_record["status"], "completed")
        self.assertIsNone(status_record["step"])
        self.assertIsNone(status_record["error"])
        self.assertEqual(
            {row["run_id"] for row in feature_rows},
            {"integration-run"},
        )
        self.assertEqual(
            {row["asset_id"] for row in feature_rows},
            {"TEST-1", "TEST-2"},
        )

    @patch("services.workflows.sprint1.engineer_and_persist_features")
    @patch("services.workflows.sprint1.generate_and_persist_raw")
    def test_workflow_runs_feature_processing_after_raw_persistence(
        self,
        generate_raw,
        engineer_features,
    ):
        raw_path = Path("data/raw/telemetry_order-test.csv")
        feature_path = Path("data/processed/features_order-test.csv")
        call_order: list[str] = []

        generate_raw.side_effect = lambda **_: (
            call_order.append("raw")
            or RawTelemetryStorageResult(
                path=raw_path,
                run_id="order-test",
                row_count=4,
            )
        )
        engineer_features.side_effect = lambda **_: (
            call_order.append("features")
            or FeatureStorageResult(
                path=feature_path,
                run_id="order-test",
                row_count=1,
            )
        )

        result = run_sprint1_workflow(
            project_root=Path("."),
            run_id="order-test",
        )

        self.assertEqual(call_order, ["raw", "features"])
        self.assertEqual(
            engineer_features.call_args.kwargs["raw_path"],
            raw_path,
        )
        self.assertEqual(result.feature_path, feature_path)

    @patch("services.workflows.sprint1.engineer_and_persist_features")
    @patch("services.workflows.sprint1.generate_and_persist_raw")
    def test_workflow_rejects_mismatched_feature_run_id(
        self,
        generate_raw,
        engineer_features,
    ):
        generate_raw.return_value = RawTelemetryStorageResult(
            path=Path("data/raw/telemetry_expected.csv"),
            run_id="expected",
            row_count=4,
        )
        engineer_features.return_value = FeatureStorageResult(
            path=Path("data/processed/features_other.csv"),
            run_id="other",
            row_count=1,
        )

        with self.assertRaisesRegex(ValueError, "preserve"):
            run_sprint1_workflow(
                project_root=Path("."),
                run_id="expected",
            )

    @patch("services.workflows.sprint1.engineer_and_persist_features")
    def test_workflow_records_and_logs_failed_step_without_suppressing_error(
        self,
        engineer_features,
    ):
        engineer_features.side_effect = RuntimeError("feature processing failed")

        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            config_path = project_root / "data" / "samples" / "asset_profiles.csv"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(ASSET_CONFIG, encoding="utf-8")

            with self.assertLogs("services.workflows.status", level="ERROR") as logs:
                with self.assertRaisesRegex(RuntimeError, "feature processing failed"):
                    run_sprint1_workflow(
                        project_root=project_root,
                        run_id="failed-run",
                        hours=1,
                    )

            status_path = (
                project_root
                / "data"
                / "workflow-status"
                / "workflow_failed-run.json"
            )
            status_record = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertEqual(status_record["run_id"], "failed-run")
        self.assertEqual(status_record["status"], "failed")
        self.assertEqual(
            status_record["step"],
            "engineer_and_persist_features",
        )
        self.assertEqual(status_record["error"], "feature processing failed")
        self.assertIn("run_id=failed-run", logs.output[0])
        self.assertIn("status=failed", logs.output[0])


if __name__ == "__main__":
    unittest.main()
