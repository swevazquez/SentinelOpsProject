from __future__ import annotations

import json
from pathlib import Path

from services.ml.rul_training import TrainingConfig, train_rul_model
from tests.unit.test_rul_training import write_metadata, write_partition


def prepare_rul_runtime(
    project_root: Path,
    *,
    training_ids: tuple[int, ...] = (1, 2, 3, 4),
    validation_ids: tuple[int, ...] = (5, 6),
) -> None:
    processed_dir = project_root / "data" / "processed" / "cmapss-fd001"
    processed_dir.mkdir(parents=True)
    training_path = processed_dir / "training.csv"
    validation_path = processed_dir / "validation.csv"
    metadata_path = processed_dir / "metadata.json"
    write_partition(training_path, training_ids)
    write_partition(validation_path, validation_ids)
    write_metadata(metadata_path, training_ids, validation_ids)
    scenario_path = project_root / "data" / "samples" / "rul_demo_scenario.json"
    scenario_path.parent.mkdir(parents=True, exist_ok=True)
    scenario_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "scenario_id": "test-held-out-engine-lifecycle",
                "dataset_id": "NASA-CMAPSS-FD001",
                "model_version": "1.0.0",
                "engine_ids": list(validation_ids[:4]),
                "checkpoint_fractions": [0.4, 0.6, 0.8, 1.0],
                "checkpoint_labels": [
                    "Early operation",
                    "Developing degradation",
                    "Maintenance approaching",
                    "Near end of useful life",
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    train_rul_model(
        training_path,
        validation_path,
        metadata_path,
        project_root / "data" / "models" / "rul-random-forest",
        config=TrainingConfig(
            model_version="1.0.0",
            rolling_window=3,
            n_estimators=8,
            max_depth=5,
        ),
    )
