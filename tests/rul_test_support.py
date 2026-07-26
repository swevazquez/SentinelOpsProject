from __future__ import annotations

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
