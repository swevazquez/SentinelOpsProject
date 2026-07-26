from __future__ import annotations

import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import joblib

from services.ml.cmapss import (
    CONTRACT_VERSION,
    DATASET_ID,
    LABELED_FIELDS,
    SENSOR_FIELDS,
    SETTING_FIELDS,
)
from services.ml.rul_training import (
    TrainingConfig,
    build_temporal_features,
    fit_temporal_feature_contract,
    train_rul_model,
)


def labeled_row(
    engine_id: int,
    cycle: int,
    *,
    final_cycle: int = 12,
    validation_only_signal: bool = False,
) -> dict[str, int | float]:
    rul = final_cycle - cycle
    row: dict[str, int | float] = {
        "engine_id": engine_id,
        "cycle": cycle,
        "rul_uncapped": rul,
        "rul": rul,
    }
    row.update({field: 0.0 for field in SETTING_FIELDS})
    row.update({field: 7.0 for field in SENSOR_FIELDS})
    row["sensor_1"] = cycle + engine_id / 100
    row["sensor_3"] = (rul * 2) + engine_id / 100
    row["sensor_4"] = cycle if validation_only_signal else 4.0
    return row


def write_partition(
    path: Path,
    engine_ids: tuple[int, ...],
    *,
    include_rul: bool = True,
    validation_only_signal: bool = False,
) -> None:
    fieldnames = list(LABELED_FIELDS)
    if not include_rul:
        fieldnames.remove("rul")
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for engine_id in engine_ids:
            for cycle in range(1, 13):
                row = labeled_row(
                    engine_id,
                    cycle,
                    validation_only_signal=validation_only_signal,
                )
                writer.writerow({field: row[field] for field in fieldnames})


def write_metadata(
    path: Path,
    training_engine_ids: tuple[int, ...],
    validation_engine_ids: tuple[int, ...],
) -> None:
    path.write_text(
        json.dumps(
            {
                "contract_version": CONTRACT_VERSION,
                "dataset_id": DATASET_ID,
                "feature_contract": {"sensor_fields": list(SENSOR_FIELDS)},
                "preprocessing_contract": {"partition_before_fitting": True},
                "split": {
                    "training_engine_ids": list(training_engine_ids),
                    "validation_engine_ids": list(validation_engine_ids),
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )


class RulTrainingTests(unittest.TestCase):
    def test_temporal_contract_uses_training_variance_and_causal_windows(self):
        training_rows = [
            labeled_row(1, cycle, final_cycle=3) for cycle in range(1, 4)
        ]
        validation_rows = [
            labeled_row(
                2,
                cycle,
                final_cycle=3,
                validation_only_signal=True,
            )
            for cycle in range(1, 4)
        ]

        contract = fit_temporal_feature_contract(training_rows, rolling_window=3)
        validation_matrix = build_temporal_features(validation_rows, contract)

        self.assertIn("sensor_1", contract.selected_sensor_fields)
        self.assertIn("sensor_3", contract.selected_sensor_fields)
        self.assertIn("sensor_4", contract.dropped_sensor_fields)
        self.assertIn("sensor_1__rolling_mean_3", contract.feature_names)
        self.assertIn("sensor_1__trend_3", contract.feature_names)
        trend_index = contract.feature_names.index("sensor_1__trend_3")
        self.assertEqual(validation_matrix.values[0][trend_index], 0.0)
        self.assertAlmostEqual(validation_matrix.values[1][trend_index], 1.0)

    def test_training_is_repeatable_and_persists_complete_versioned_artifact(self):
        training_ids = (1, 2, 3, 4, 5, 6)
        validation_ids = (7, 8)
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            training_path = root / "training.csv"
            validation_path = root / "validation.csv"
            metadata_path = root / "metadata.json"
            write_partition(training_path, training_ids)
            write_partition(
                validation_path,
                validation_ids,
                validation_only_signal=True,
            )
            write_metadata(metadata_path, training_ids, validation_ids)
            config = TrainingConfig(
                model_version="1.2.0",
                seed=42,
                rolling_window=3,
                n_estimators=40,
                max_depth=8,
            )

            first = train_rul_model(
                training_path,
                validation_path,
                metadata_path,
                root / "models-first",
                config=config,
            )
            second = train_rul_model(
                training_path,
                validation_path,
                metadata_path,
                root / "models-second",
                config=config,
            )
            first_metadata = json.loads(
                first.metadata_path.read_text(encoding="utf-8")
            )
            second_metadata = json.loads(
                second.metadata_path.read_text(encoding="utf-8")
            )
            evaluation_rows = [
                labeled_row(
                    7,
                    cycle,
                    validation_only_signal=True,
                )
                for cycle in range(1, 13)
            ]
            evaluation_contract = fit_temporal_feature_contract(
                [
                    labeled_row(engine_id, cycle)
                    for engine_id in training_ids
                    for cycle in range(1, 13)
                ],
                rolling_window=config.rolling_window,
            )
            evaluation_matrix = build_temporal_features(
                evaluation_rows,
                evaluation_contract,
            )
            first_payload = joblib.load(first.model_path)
            second_payload = joblib.load(second.model_path)

            self.assertEqual(first.metrics, second.metrics)
            self.assertEqual(
                first_payload["model"].predict(evaluation_matrix.values).tolist(),
                second_payload["model"].predict(evaluation_matrix.values).tolist(),
            )
            self.assertEqual(
                first_metadata["feature_importance"],
                second_metadata["feature_importance"],
            )
            self.assertTrue(first.model_path.is_file())
            self.assertEqual(first_metadata["model_version"], "1.2.0")
            self.assertEqual(first_metadata["dataset"]["dataset_id"], DATASET_ID)
            self.assertEqual(first_metadata["training"]["seed"], 42)
            self.assertEqual(
                first_metadata["preprocessing"]["fit_partition"],
                "training engines only",
            )
            self.assertNotIn(
                "sensor_4",
                first_metadata["preprocessing"]["selected_sensor_fields"],
            )
            self.assertIn(
                "sensor_4",
                first_metadata["preprocessing"]["dropped_sensor_fields"],
            )
            self.assertEqual(
                first_metadata["evaluation"],
                second_metadata["evaluation"],
            )
            self.assertIn(
                "per_engine",
                first_metadata["evaluation"]["random_forest"],
            )
            self.assertIn(
                "median_rul_baseline",
                first_metadata["evaluation"],
            )
            self.assertEqual(
                len(first_metadata["files"]["model"]["sha256"]),
                64,
            )

    def test_incomplete_training_partition_fails_without_artifact(self):
        training_ids = (1, 2)
        validation_ids = (3,)
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            training_path = root / "training.csv"
            validation_path = root / "validation.csv"
            metadata_path = root / "metadata.json"
            output_root = root / "models"
            write_partition(training_path, training_ids, include_rul=False)
            write_partition(validation_path, validation_ids)
            write_metadata(metadata_path, training_ids, validation_ids)

            with self.assertRaisesRegex(ValueError, "missing required labeled fields"):
                train_rul_model(
                    training_path,
                    validation_path,
                    metadata_path,
                    output_root,
                    config=TrainingConfig(n_estimators=10),
                )

            self.assertFalse(output_root.exists())

    def test_partition_overlap_is_rejected_before_model_creation(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            training_path = root / "training.csv"
            validation_path = root / "validation.csv"
            metadata_path = root / "metadata.json"
            output_root = root / "models"
            write_partition(training_path, (1, 2))
            write_partition(validation_path, (2, 3))
            write_metadata(metadata_path, (1, 2), (2, 3))

            with self.assertRaisesRegex(ValueError, "share engine IDs"):
                train_rul_model(
                    training_path,
                    validation_path,
                    metadata_path,
                    output_root,
                    config=TrainingConfig(n_estimators=10),
                )

            self.assertFalse(output_root.exists())


if __name__ == "__main__":
    unittest.main()
