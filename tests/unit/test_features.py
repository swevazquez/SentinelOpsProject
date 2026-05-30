import csv
from pathlib import Path
import tempfile
import unittest

from services.spark_jobs.features import (
    FEATURE_FIELDS,
    engineer_features,
    persist_feature_rows,
    write_features_csv,
)


class FeatureEngineeringTests(unittest.TestCase):
    def test_engineer_features_groups_raw_telemetry_by_run_and_asset(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        raw_path = Path(temp_dir.name) / "raw.csv"

        with raw_path.open("w", newline="", encoding="utf-8") as output_file:
            writer = csv.DictWriter(
                output_file,
                fieldnames=[
                    "run_id",
                    "asset_id",
                    "timestamp",
                    "temperature_c",
                    "vibration_mm_s",
                    "pressure_kpa",
                    "runtime_hours",
                    "failure_within_7d",
                ],
            )
            writer.writeheader()
            writer.writerows(
                [
                    {
                        "run_id": "run-1",
                        "asset_id": "A-100",
                        "timestamp": "2026-05-17T00:00:00Z",
                        "temperature_c": "70.00",
                        "vibration_mm_s": "2.00",
                        "pressure_kpa": "210.00",
                        "runtime_hours": "10",
                        "failure_within_7d": "0",
                    },
                    {
                        "run_id": "run-1",
                        "asset_id": "A-100",
                        "timestamp": "2026-05-17T01:00:00Z",
                        "temperature_c": "74.00",
                        "vibration_mm_s": "4.00",
                        "pressure_kpa": "214.00",
                        "runtime_hours": "11",
                        "failure_within_7d": "1",
                    },
                ]
            )

        features = engineer_features(raw_path)

        self.assertEqual(
            features,
            [
                {
                    "run_id": "run-1",
                    "asset_id": "A-100",
                    "sample_count": "2",
                    "first_timestamp": "2026-05-17T00:00:00Z",
                    "last_timestamp": "2026-05-17T01:00:00Z",
                    "avg_temperature_c": "72.00",
                    "max_temperature_c": "74.00",
                    "avg_vibration_mm_s": "3.00",
                    "max_vibration_mm_s": "4.00",
                    "avg_pressure_kpa": "212.00",
                    "min_runtime_hours": "10",
                    "max_runtime_hours": "11",
                    "failure_observed": "1",
                }
            ],
        )

    def test_write_features_csv_creates_parent_directories(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        output_path = Path(temp_dir.name) / "processed" / "features.csv"

        write_features_csv(
            [
                {
                    "run_id": "run-1",
                    "asset_id": "A-100",
                    "sample_count": "1",
                    "first_timestamp": "2026-05-17T00:00:00Z",
                    "last_timestamp": "2026-05-17T00:00:00Z",
                    "avg_temperature_c": "70.00",
                    "max_temperature_c": "70.00",
                    "avg_vibration_mm_s": "2.00",
                    "max_vibration_mm_s": "2.00",
                    "avg_pressure_kpa": "210.00",
                    "min_runtime_hours": "10",
                    "max_runtime_hours": "10",
                    "failure_observed": "0",
                }
            ],
            output_path,
        )

        self.assertTrue(output_path.exists())

    def test_persist_feature_rows_writes_configured_storage_location(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)

        result = persist_feature_rows(
            [
                {
                    "run_id": "run-1",
                    "asset_id": "A-100",
                    "sample_count": "1",
                    "first_timestamp": "2026-05-17T00:00:00Z",
                    "last_timestamp": "2026-05-17T00:00:00Z",
                    "avg_temperature_c": "70.00",
                    "max_temperature_c": "70.00",
                    "avg_vibration_mm_s": "2.00",
                    "max_vibration_mm_s": "2.00",
                    "avg_pressure_kpa": "210.00",
                    "min_runtime_hours": "10",
                    "max_runtime_hours": "10",
                    "failure_observed": "0",
                }
            ],
            Path(temp_dir.name) / "processed",
        )

        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(result.row_count, 1)
        self.assertEqual(result.path.name, "features_run-1.csv")

        with result.path.open(newline="", encoding="utf-8") as input_file:
            reader = csv.DictReader(input_file)
            stored_rows = list(reader)

        self.assertEqual(reader.fieldnames, FEATURE_FIELDS)
        self.assertEqual(stored_rows[0]["asset_id"], "A-100")

    def test_engineer_features_rejects_missing_raw_fields(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        raw_path = Path(temp_dir.name) / "raw.csv"

        with raw_path.open("w", newline="", encoding="utf-8") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=["run_id", "asset_id"])
            writer.writeheader()
            writer.writerow({"run_id": "run-1", "asset_id": "A-100"})

        with self.assertRaisesRegex(ValueError, "missing required fields"):
            engineer_features(raw_path)

    def test_engineer_features_rejects_empty_raw_input(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        raw_path = Path(temp_dir.name) / "raw.csv"

        with raw_path.open("w", newline="", encoding="utf-8") as output_file:
            writer = csv.DictWriter(
                output_file,
                fieldnames=[
                    "run_id",
                    "asset_id",
                    "timestamp",
                    "temperature_c",
                    "vibration_mm_s",
                    "pressure_kpa",
                    "runtime_hours",
                    "failure_within_7d",
                ],
            )
            writer.writeheader()

        with self.assertRaisesRegex(ValueError, "at least one row"):
            engineer_features(raw_path)


if __name__ == "__main__":
    unittest.main()
