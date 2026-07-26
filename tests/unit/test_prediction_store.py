import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from services.ml.prediction_store import CsvPredictionRepository
from services.ml.scoring import LEGACY_PREDICTION_FIELDS


def prediction_row(
    *,
    asset_id: str = "A-100",
    run_id: str = "run-1",
    scored_at: str = "2026-06-15T15:00:00Z",
    risk_score: str = "0.5000",
) -> dict[str, str]:
    return {
        "run_id": run_id,
        "asset_id": asset_id,
        "prediction_type": "risk_baseline",
        "model_name": "sentinelops-risk-baseline",
        "model_version": "1.0.0",
        "scored_at": scored_at,
        "source_feature_path": "data/processed/features_run-1.csv",
        "source_feature_sha256": "a" * 64,
        "model_artifact_sha256": "",
        "dataset_id": "",
        "feature_contract_version": "",
        "remaining_useful_life_cycles": "",
        "risk_score": risk_score,
        "health_score": "0.5000",
        "asset_status": "warning",
        "maintenance_priority": "high",
        "recommended_action": "Schedule maintenance within 24 hours.",
    }


class CsvPredictionRepositoryTests(unittest.TestCase):
    def test_save_and_get_by_run_preserve_prediction_fields(self):
        with TemporaryDirectory() as temp_dir:
            repository = CsvPredictionRepository(Path(temp_dir))
            rows = [
                prediction_row(asset_id="A-100"),
                prediction_row(asset_id="A-101"),
            ]

            result = repository.save(rows)
            stored_rows = repository.get_by_run("run-1")

        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(result.row_count, 2)
        self.assertEqual(result.path.name, "predictions_run-1.csv")
        self.assertEqual(stored_rows, rows)

    def test_get_by_asset_returns_newest_prediction_first(self):
        with TemporaryDirectory() as temp_dir:
            repository = CsvPredictionRepository(Path(temp_dir))
            repository.save(
                [
                    prediction_row(
                        run_id="run-1",
                        scored_at="2026-06-15T15:00:00Z",
                    )
                ]
            )
            repository.save(
                [
                    prediction_row(
                        run_id="run-2",
                        scored_at="2026-06-16T15:00:00Z",
                    ),
                    prediction_row(asset_id="A-200", run_id="run-2"),
                ]
            )

            predictions = repository.get_by_asset("A-100")

        self.assertEqual(
            [prediction["run_id"] for prediction in predictions],
            ["run-2", "run-1"],
        )

    def test_missing_run_returns_empty_result(self):
        with TemporaryDirectory() as temp_dir:
            repository = CsvPredictionRepository(Path(temp_dir))

            self.assertEqual(repository.get_by_run("missing"), [])

    def test_legacy_baseline_predictions_remain_readable(self):
        with TemporaryDirectory() as temp_dir:
            storage_dir = Path(temp_dir)
            path = storage_dir / "predictions_legacy-run.csv"
            row = prediction_row(run_id="legacy-run")
            with path.open("w", newline="", encoding="utf-8") as output_file:
                writer = csv.DictWriter(
                    output_file,
                    fieldnames=LEGACY_PREDICTION_FIELDS,
                )
                writer.writeheader()
                writer.writerow(
                    {field: row[field] for field in LEGACY_PREDICTION_FIELDS}
                )

            stored_rows = CsvPredictionRepository(storage_dir).get_by_run(
                "legacy-run"
            )

        self.assertEqual(stored_rows[0]["prediction_type"], "risk_baseline")
        self.assertEqual(stored_rows[0]["health_score"], "0.5000")
        self.assertEqual(stored_rows[0]["remaining_useful_life_cycles"], "")

    def test_save_rejects_missing_prediction_fields(self):
        with TemporaryDirectory() as temp_dir:
            repository = CsvPredictionRepository(Path(temp_dir))
            row = prediction_row()
            del row["maintenance_priority"]

            with self.assertRaisesRegex(ValueError, "missing required fields"):
                repository.save([row])

    def test_save_rejects_unsafe_run_id(self):
        with TemporaryDirectory() as temp_dir:
            repository = CsvPredictionRepository(Path(temp_dir))

            with self.assertRaisesRegex(ValueError, "file-safe"):
                repository.save([prediction_row(run_id="../other")])

    def test_save_rejects_out_of_range_risk_score(self):
        with TemporaryDirectory() as temp_dir:
            repository = CsvPredictionRepository(Path(temp_dir))

            with self.assertRaisesRegex(ValueError, "between 0 and 1"):
                repository.save([prediction_row(risk_score="1.5000")])

    def test_save_rejects_invalid_source_fingerprint(self):
        with TemporaryDirectory() as temp_dir:
            repository = CsvPredictionRepository(Path(temp_dir))
            row = prediction_row()
            row["source_feature_sha256"] = "not-a-sha256"

            with self.assertRaisesRegex(ValueError, "SHA-256 is invalid"):
                repository.save([row])


if __name__ == "__main__":
    unittest.main()
