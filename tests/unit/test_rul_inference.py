from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from services.ml.cmapss import DATASET_ID
from services.ml.rul_inference import (
    load_rul_artifact,
    rul_maintenance_indicators,
    score_rul_trajectory_file,
)
from services.ml.rul_training import ARTIFACT_SCHEMA_VERSION, TrainingConfig, train_rul_model
from tests.unit.test_rul_training import write_metadata, write_partition


class RulInferenceTests(unittest.TestCase):
    def _train_artifact(self, root: Path) -> tuple[Path, Path]:
        training_ids = (1, 2, 3, 4)
        validation_ids = (5, 6)
        training_path = root / "training.csv"
        validation_path = root / "validation.csv"
        metadata_path = root / "metadata.json"
        write_partition(training_path, training_ids)
        write_partition(validation_path, validation_ids)
        write_metadata(metadata_path, training_ids, validation_ids)
        result = train_rul_model(
            training_path,
            validation_path,
            metadata_path,
            root / "models",
            config=TrainingConfig(
                model_version="1.0.0",
                rolling_window=3,
                n_estimators=8,
                max_depth=5,
            ),
        )
        return result.artifact_dir, validation_path

    def test_training_artifact_scores_latest_cycle_for_each_engine(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact_dir, trajectory_path = self._train_artifact(root)

            result = score_rul_trajectory_file(
                trajectory_path,
                artifact_dir,
                run_id="rul-run",
                scored_at=datetime(2026, 7, 26, 14, 0, tzinfo=UTC),
            )

        self.assertEqual(result.trajectory_row_count, 24)
        self.assertEqual(
            [row["asset_id"] for row in result.predictions],
            ["FD001-ENGINE-005", "FD001-ENGINE-006"],
        )
        for prediction in result.predictions:
            self.assertEqual(prediction["run_id"], "rul-run")
            self.assertEqual(prediction["prediction_type"], "rul")
            self.assertEqual(prediction["model_version"], "1.0.0")
            self.assertEqual(prediction["dataset_id"], DATASET_ID)
            self.assertEqual(
                prediction["feature_contract_version"],
                ARTIFACT_SCHEMA_VERSION,
            )
            self.assertEqual(prediction["scored_at"], "2026-07-26T14:00:00Z")
            self.assertGreaterEqual(
                float(prediction["remaining_useful_life_cycles"]),
                0.0,
            )
            self.assertLessEqual(float(prediction["risk_score"]), 1.0)
            self.assertGreaterEqual(float(prediction["health_score"]), 0.0)
            self.assertEqual(len(prediction["model_artifact_sha256"]), 64)

    def test_rul_mapping_is_bounded_and_matches_maintenance_thresholds(self) -> None:
        cases = (
            (-10.0, "critical", "immediate", 1.0, 0.0),
            (31.25, "critical", "immediate", 0.75, 0.25),
            (62.5, "warning", "high", 0.5, 0.5),
            (93.75, "watch", "medium", 0.25, 0.75),
            (125.0, "healthy", "routine", 0.0, 1.0),
            (200.0, "healthy", "routine", 0.0, 1.0),
        )
        for rul, status, priority, risk, health in cases:
            with self.subTest(rul=rul):
                indicators = rul_maintenance_indicators(rul)
                self.assertEqual(indicators["asset_status"], status)
                self.assertEqual(indicators["maintenance_priority"], priority)
                self.assertEqual(float(indicators["risk_score"]), risk)
                self.assertEqual(float(indicators["health_score"]), health)

    def test_corrupt_model_is_rejected_before_inference(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact_dir, _ = self._train_artifact(root)
            model_path = artifact_dir / "model.joblib"
            model_path.write_bytes(model_path.read_bytes() + b"corrupt")

            with self.assertRaisesRegex(ValueError, "checksum"):
                load_rul_artifact(artifact_dir)

    def test_incompatible_feature_contract_is_rejected(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact_dir, _ = self._train_artifact(root)
            metadata_path = artifact_dir / "metadata.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["preprocessing"]["feature_names"] = ["unexpected"]
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "feature contract"):
                load_rul_artifact(artifact_dir)


if __name__ == "__main__":
    unittest.main()
