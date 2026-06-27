from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.demo_performance import (
    DemoPerformanceError,
    run_demo_performance_validation,
    write_report,
)


ASSET_CONFIG = "\n".join(
    [
        "asset_id,base_temperature_c,base_vibration_mm_s,base_pressure_kpa,runtime_hours,failure_risk",
        "TEST-1,70.0,2.5,220.0,100,0.1",
        "TEST-2,84.0,5.5,248.0,2600,0.6",
    ]
)


class DemoPerformanceTests(unittest.TestCase):
    def test_demo_performance_validation_records_complete_outputs(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            config_path = project_root / "data" / "samples" / "asset_profiles.csv"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(ASSET_CONFIG, encoding="utf-8")

            report = run_demo_performance_validation(
                project_root=project_root,
                runs=2,
                hours=4,
                max_seconds=5.0,
                run_prefix="test-demo",
            )
            report_path = write_report(
                report,
                project_root / "data" / "performance" / "report.json",
            )
            report_payload = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertTrue(report.passed)
        self.assertEqual(report.runs, 2)
        self.assertEqual(report.hours, 4)
        self.assertEqual(len(report.measurements), 2)
        self.assertGreaterEqual(report.max_duration_seconds, 0)
        self.assertEqual(report_payload["runs"], 2)
        for measurement in report.measurements:
            self.assertTrue(measurement.passed)
            self.assertEqual(measurement.raw_row_count, 8)
            self.assertEqual(measurement.feature_row_count, 2)
            self.assertEqual(measurement.prediction_row_count, 2)
            self.assertEqual(measurement.workflow_status, "completed")

    def test_demo_performance_validation_rejects_incomplete_threshold(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            config_path = project_root / "data" / "samples" / "asset_profiles.csv"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(ASSET_CONFIG, encoding="utf-8")

            with self.assertRaises(DemoPerformanceError):
                run_demo_performance_validation(
                    project_root=project_root,
                    runs=1,
                    hours=4,
                    max_seconds=0.0001,
                    run_prefix="slow-demo",
                )

    def test_demo_performance_validation_rejects_invalid_parameters(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            with self.assertRaises(ValueError):
                run_demo_performance_validation(project_root=project_root, runs=0)
            with self.assertRaises(ValueError):
                run_demo_performance_validation(project_root=project_root, hours=0)
            with self.assertRaises(ValueError):
                run_demo_performance_validation(
                    project_root=project_root,
                    max_seconds=0,
                )


if __name__ == "__main__":
    unittest.main()
