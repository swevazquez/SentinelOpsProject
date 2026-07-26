from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
import shutil
from statistics import median, pvariance
import tempfile
from typing import Any

import joblib
import numpy
import sklearn
from sklearn.ensemble import RandomForestRegressor

from services.ml.cmapss import (
    CONTRACT_VERSION,
    DATASET_ID,
    LABELED_FIELDS,
    SENSOR_FIELDS,
    SETTING_FIELDS,
    file_sha256,
)


MODEL_TYPE = "random_forest_rul_regressor"
ARTIFACT_SCHEMA_VERSION = "1.0.0"
DEFAULT_MODEL_VERSION = "1.0.0"
DEFAULT_SEED = 42
DEFAULT_ROLLING_WINDOW = 5
DEFAULT_N_ESTIMATORS = 80
DEFAULT_MAX_DEPTH = 14
DEFAULT_MIN_SENSOR_VARIANCE = 1e-12
SEMANTIC_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


NumericRow = dict[str, int | float]


@dataclass(frozen=True)
class TrainingConfig:
    model_version: str = DEFAULT_MODEL_VERSION
    seed: int = DEFAULT_SEED
    rolling_window: int = DEFAULT_ROLLING_WINDOW
    n_estimators: int = DEFAULT_N_ESTIMATORS
    max_depth: int | None = DEFAULT_MAX_DEPTH
    min_sensor_variance: float = DEFAULT_MIN_SENSOR_VARIANCE


@dataclass(frozen=True)
class TemporalFeatureContract:
    selected_sensor_fields: tuple[str, ...]
    dropped_sensor_fields: tuple[str, ...]
    sensor_variances: dict[str, float]
    feature_names: tuple[str, ...]
    rolling_window: int


@dataclass(frozen=True)
class FeatureMatrix:
    values: list[list[float]]
    targets: list[float]
    engine_ids: list[int]


@dataclass(frozen=True)
class TrainingResult:
    artifact_dir: Path
    model_path: Path
    metadata_path: Path
    metrics: dict[str, Any]
    selected_sensor_fields: tuple[str, ...]
    feature_names: tuple[str, ...]


def _read_labeled_partition(path: Path) -> list[NumericRow]:
    if not path.is_file():
        raise ValueError(f"labeled C-MAPSS partition does not exist: {path}")

    rows: list[NumericRow] = []
    observed_keys: set[tuple[int, int]] = set()
    with path.open(newline="", encoding="utf-8") as input_file:
        reader = csv.DictReader(input_file)
        fieldnames = set(reader.fieldnames or ())
        missing_fields = [field for field in LABELED_FIELDS if field not in fieldnames]
        if missing_fields:
            raise ValueError(
                f"{path} is missing required labeled fields: "
                + ", ".join(missing_fields)
            )

        for line_number, raw_row in enumerate(reader, start=2):
            row: NumericRow = {}
            for field in LABELED_FIELDS:
                value = raw_row.get(field)
                try:
                    numeric_value = float(value) if value is not None else math.nan
                except ValueError as error:
                    raise ValueError(
                        f"{path}:{line_number} field {field} must be numeric"
                    ) from error
                if not math.isfinite(numeric_value):
                    raise ValueError(
                        f"{path}:{line_number} field {field} must be finite"
                    )
                row[field] = numeric_value

            for identifier in ("engine_id", "cycle", "rul_uncapped", "rul"):
                value = float(row[identifier])
                if not value.is_integer():
                    raise ValueError(
                        f"{path}:{line_number} field {identifier} must be an integer"
                    )
                row[identifier] = int(value)

            engine_id = int(row["engine_id"])
            cycle = int(row["cycle"])
            if engine_id < 1 or cycle < 1:
                raise ValueError(
                    f"{path}:{line_number} engine_id and cycle must be positive"
                )
            if int(row["rul"]) < 0 or int(row["rul_uncapped"]) < 0:
                raise ValueError(
                    f"{path}:{line_number} RUL labels must be nonnegative"
                )

            key = (engine_id, cycle)
            if key in observed_keys:
                raise ValueError(
                    f"{path}:{line_number} duplicates engine {engine_id} cycle {cycle}"
                )
            observed_keys.add(key)
            rows.append(row)

    if not rows:
        raise ValueError(f"{path} must contain at least one labeled row")

    cycles_by_engine: dict[int, list[int]] = {}
    for row in rows:
        cycles_by_engine.setdefault(int(row["engine_id"]), []).append(
            int(row["cycle"])
        )
    for engine_id, cycles in cycles_by_engine.items():
        expected_cycles = list(range(1, max(cycles) + 1))
        if sorted(cycles) != expected_cycles:
            raise ValueError(
                f"{path} engine {engine_id} cycles must be contiguous and begin at 1"
            )

    return sorted(rows, key=lambda row: (int(row["engine_id"]), int(row["cycle"])))


def _load_data_contract(metadata_path: Path) -> dict[str, Any]:
    if not metadata_path.is_file():
        raise ValueError(f"C-MAPSS metadata does not exist: {metadata_path}")
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise ValueError(f"C-MAPSS metadata is not valid JSON: {metadata_path}") from error

    if metadata.get("dataset_id") != DATASET_ID:
        raise ValueError(
            f"expected dataset_id {DATASET_ID}, found {metadata.get('dataset_id')!r}"
        )
    if metadata.get("contract_version") != CONTRACT_VERSION:
        raise ValueError(
            "incompatible C-MAPSS contract version: "
            f"expected {CONTRACT_VERSION}, "
            f"found {metadata.get('contract_version')!r}"
        )
    feature_contract = metadata.get("feature_contract", {})
    if feature_contract.get("sensor_fields") != list(SENSOR_FIELDS):
        raise ValueError("C-MAPSS metadata has an incompatible sensor-field contract")
    return metadata


def _validate_partition_contract(
    training_rows: list[NumericRow],
    validation_rows: list[NumericRow],
    metadata: dict[str, Any],
) -> None:
    training_ids = {int(row["engine_id"]) for row in training_rows}
    validation_ids = {int(row["engine_id"]) for row in validation_rows}
    overlap = training_ids & validation_ids
    if overlap:
        raise ValueError(
            "training and validation partitions share engine IDs: "
            + ", ".join(str(engine_id) for engine_id in sorted(overlap))
        )

    split = metadata.get("split", {})
    expected_training_ids = set(split.get("training_engine_ids", ()))
    expected_validation_ids = set(split.get("validation_engine_ids", ()))
    if training_ids != expected_training_ids:
        raise ValueError("training engine IDs do not match the C-MAPSS metadata")
    if validation_ids != expected_validation_ids:
        raise ValueError("validation engine IDs do not match the C-MAPSS metadata")
    if not metadata.get("preprocessing_contract", {}).get(
        "partition_before_fitting"
    ):
        raise ValueError("C-MAPSS metadata does not require partition-before-fitting")


def _validate_config(config: TrainingConfig) -> None:
    if not SEMANTIC_VERSION_PATTERN.fullmatch(config.model_version):
        raise ValueError("model_version must use semantic MAJOR.MINOR.PATCH format")
    if config.rolling_window < 2:
        raise ValueError("rolling_window must be at least 2")
    if config.n_estimators < 1:
        raise ValueError("n_estimators must be positive")
    if config.max_depth is not None and config.max_depth < 1:
        raise ValueError("max_depth must be positive when provided")
    if config.min_sensor_variance < 0:
        raise ValueError("min_sensor_variance cannot be negative")


def fit_temporal_feature_contract(
    training_rows: list[NumericRow],
    *,
    rolling_window: int = DEFAULT_ROLLING_WINDOW,
    min_sensor_variance: float = DEFAULT_MIN_SENSOR_VARIANCE,
) -> TemporalFeatureContract:
    if not training_rows:
        raise ValueError("feature selection requires training rows")
    if rolling_window < 2:
        raise ValueError("rolling_window must be at least 2")

    sensor_variances = {
        field: float(pvariance(float(row[field]) for row in training_rows))
        for field in SENSOR_FIELDS
    }
    selected_sensor_fields = tuple(
        field
        for field in SENSOR_FIELDS
        if sensor_variances[field] > min_sensor_variance
    )
    dropped_sensor_fields = tuple(
        field for field in SENSOR_FIELDS if field not in selected_sensor_fields
    )
    if not selected_sensor_fields:
        raise ValueError(
            "training partition has no informative sensor fields above the "
            "configured variance threshold"
        )

    feature_names: list[str] = ["cycle", *SETTING_FIELDS]
    for field in selected_sensor_fields:
        feature_names.extend(
            (
                field,
                f"{field}__rolling_mean_{rolling_window}",
                f"{field}__rolling_std_{rolling_window}",
                f"{field}__trend_{rolling_window}",
            )
        )
    return TemporalFeatureContract(
        selected_sensor_fields=selected_sensor_fields,
        dropped_sensor_fields=dropped_sensor_fields,
        sensor_variances=sensor_variances,
        feature_names=tuple(feature_names),
        rolling_window=rolling_window,
    )


def _trend(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    x_mean = (len(values) - 1) / 2
    y_mean = sum(values) / len(values)
    denominator = sum((index - x_mean) ** 2 for index in range(len(values)))
    return (
        sum(
            (index - x_mean) * (value - y_mean)
            for index, value in enumerate(values)
        )
        / denominator
    )


def build_temporal_features(
    rows: list[NumericRow],
    contract: TemporalFeatureContract,
) -> FeatureMatrix:
    if not rows:
        raise ValueError("temporal feature generation requires labeled rows")

    values: list[list[float]] = []
    targets: list[float] = []
    engine_ids: list[int] = []
    rows_by_engine: dict[int, list[NumericRow]] = {}
    for row in rows:
        rows_by_engine.setdefault(int(row["engine_id"]), []).append(row)

    for engine_id in sorted(rows_by_engine):
        trajectory = sorted(
            rows_by_engine[engine_id], key=lambda row: int(row["cycle"])
        )
        for row_index, row in enumerate(trajectory):
            first_window_index = max(0, row_index - contract.rolling_window + 1)
            window = trajectory[first_window_index : row_index + 1]
            feature_row = [
                float(row["cycle"]),
                *(float(row[field]) for field in SETTING_FIELDS),
            ]
            for field in contract.selected_sensor_fields:
                sensor_window = [float(window_row[field]) for window_row in window]
                feature_row.extend(
                    (
                        float(row[field]),
                        sum(sensor_window) / len(sensor_window),
                        math.sqrt(float(pvariance(sensor_window))),
                        _trend(sensor_window),
                    )
                )
            if not all(math.isfinite(value) for value in feature_row):
                raise ValueError(
                    f"engine {engine_id} cycle {row['cycle']} produced "
                    "non-finite temporal features"
                )
            values.append(feature_row)
            targets.append(float(row["rul"]))
            engine_ids.append(engine_id)

    return FeatureMatrix(values=values, targets=targets, engine_ids=engine_ids)


def _error_metrics(actual: list[float], predicted: list[float]) -> dict[str, float]:
    if len(actual) != len(predicted) or not actual:
        raise ValueError("metric inputs must be nonempty and have equal length")
    errors = [prediction - target for target, prediction in zip(actual, predicted)]
    return {
        "mae": sum(abs(error) for error in errors) / len(errors),
        "rmse": math.sqrt(sum(error**2 for error in errors) / len(errors)),
    }


def _engine_level_metrics(
    actual: list[float],
    predicted: list[float],
    engine_ids: list[int],
) -> dict[str, Any]:
    if not (len(actual) == len(predicted) == len(engine_ids)):
        raise ValueError("engine-level metric inputs must have equal length")

    grouped: dict[int, tuple[list[float], list[float]]] = {}
    for target, prediction, engine_id in zip(actual, predicted, engine_ids):
        engine_actual, engine_predicted = grouped.setdefault(engine_id, ([], []))
        engine_actual.append(target)
        engine_predicted.append(prediction)

    per_engine = {
        str(engine_id): {
            "rows": len(engine_actual),
            **_error_metrics(engine_actual, engine_predicted),
        }
        for engine_id, (engine_actual, engine_predicted) in sorted(grouped.items())
    }
    return {
        "overall": _error_metrics(actual, predicted),
        "macro_engine": {
            "mae": sum(item["mae"] for item in per_engine.values())
            / len(per_engine),
            "rmse": sum(item["rmse"] for item in per_engine.values())
            / len(per_engine),
        },
        "per_engine": per_engine,
    }


def _sorted_feature_importance(
    feature_names: tuple[str, ...],
    importances: list[float],
) -> list[dict[str, float | str]]:
    return sorted(
        (
            {"feature": feature, "importance": float(importance)}
            for feature, importance in zip(feature_names, importances, strict=True)
        ),
        key=lambda item: (-float(item["importance"]), str(item["feature"])),
    )


def train_rul_model(
    training_path: Path,
    validation_path: Path,
    data_metadata_path: Path,
    output_root: Path,
    *,
    config: TrainingConfig = TrainingConfig(),
) -> TrainingResult:
    _validate_config(config)
    artifact_dir = output_root / config.model_version
    if artifact_dir.exists():
        raise ValueError(
            f"model artifact version already exists and is immutable: {artifact_dir}"
        )

    training_rows = _read_labeled_partition(training_path)
    validation_rows = _read_labeled_partition(validation_path)
    data_metadata = _load_data_contract(data_metadata_path)
    _validate_partition_contract(training_rows, validation_rows, data_metadata)

    feature_contract = fit_temporal_feature_contract(
        training_rows,
        rolling_window=config.rolling_window,
        min_sensor_variance=config.min_sensor_variance,
    )
    training_matrix = build_temporal_features(training_rows, feature_contract)
    validation_matrix = build_temporal_features(validation_rows, feature_contract)

    model = RandomForestRegressor(
        n_estimators=config.n_estimators,
        max_depth=config.max_depth,
        random_state=config.seed,
        n_jobs=1,
    )
    model.fit(training_matrix.values, training_matrix.targets)
    model_predictions = [
        max(0.0, float(value)) for value in model.predict(validation_matrix.values)
    ]
    baseline_value = float(median(training_matrix.targets))
    baseline_predictions = [baseline_value] * len(validation_matrix.targets)
    metrics = {
        "random_forest": _engine_level_metrics(
            validation_matrix.targets,
            model_predictions,
            validation_matrix.engine_ids,
        ),
        "median_rul_baseline": {
            "training_median_rul": baseline_value,
            **_engine_level_metrics(
                validation_matrix.targets,
                baseline_predictions,
                validation_matrix.engine_ids,
            ),
        },
    }

    output_root.mkdir(parents=True, exist_ok=True)
    temporary_dir = Path(
        tempfile.mkdtemp(prefix=f".{config.model_version}-", dir=output_root)
    )
    try:
        model_path = temporary_dir / "model.joblib"
        metadata_path = temporary_dir / "metadata.json"
        joblib.dump(
            {
                "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
                "model_version": config.model_version,
                "model": model,
                "feature_names": feature_contract.feature_names,
                "selected_sensor_fields": feature_contract.selected_sensor_fields,
                "rolling_window": feature_contract.rolling_window,
            },
            model_path,
        )
        feature_importance = _sorted_feature_importance(
            feature_contract.feature_names,
            [float(value) for value in model.feature_importances_],
        )
        artifact_metadata = {
            "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
            "model_version": config.model_version,
            "model_type": MODEL_TYPE,
            "dataset": {
                "dataset_id": data_metadata["dataset_id"],
                "contract_version": data_metadata["contract_version"],
                "metadata_sha256": file_sha256(data_metadata_path),
                "training_partition_sha256": file_sha256(training_path),
                "validation_partition_sha256": file_sha256(validation_path),
            },
            "training": {
                "seed": config.seed,
                "n_estimators": config.n_estimators,
                "max_depth": config.max_depth,
                "training_rows": len(training_rows),
                "training_engine_ids": sorted(
                    {int(row["engine_id"]) for row in training_rows}
                ),
                "validation_rows": len(validation_rows),
                "validation_engine_ids": sorted(
                    {int(row["engine_id"]) for row in validation_rows}
                ),
                "libraries": {
                    "joblib": joblib.__version__,
                    "numpy": numpy.__version__,
                    "scikit-learn": sklearn.__version__,
                },
            },
            "preprocessing": {
                "fit_partition": "training engines only",
                "partition_before_fitting": True,
                "rolling_window": feature_contract.rolling_window,
                "rolling_direction": "causal, current and prior cycles only",
                "sensor_variance_threshold": config.min_sensor_variance,
                "sensor_variances": feature_contract.sensor_variances,
                "selected_sensor_fields": list(
                    feature_contract.selected_sensor_fields
                ),
                "dropped_sensor_fields": list(feature_contract.dropped_sensor_fields),
                "feature_names": list(feature_contract.feature_names),
            },
            "evaluation": metrics,
            "feature_importance": feature_importance,
            "files": {
                "model": {
                    "path": model_path.name,
                    "sha256": file_sha256(model_path),
                },
                "metadata": {"path": metadata_path.name},
            },
        }
        metadata_path.write_text(
            json.dumps(artifact_metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary_dir.replace(artifact_dir)
    except Exception:
        shutil.rmtree(temporary_dir, ignore_errors=True)
        raise

    return TrainingResult(
        artifact_dir=artifact_dir,
        model_path=artifact_dir / "model.joblib",
        metadata_path=artifact_dir / "metadata.json",
        metrics=metrics,
        selected_sensor_fields=feature_contract.selected_sensor_fields,
        feature_names=feature_contract.feature_names,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train and evaluate the SentinelOps Random Forest RUL model."
    )
    parser.add_argument(
        "--training-file",
        type=Path,
        default=Path("data/processed/cmapss-fd001/training.csv"),
    )
    parser.add_argument(
        "--validation-file",
        type=Path,
        default=Path("data/processed/cmapss-fd001/validation.csv"),
    )
    parser.add_argument(
        "--data-metadata",
        type=Path,
        default=Path("data/processed/cmapss-fd001/metadata.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/models/rul-random-forest"),
    )
    parser.add_argument("--model-version", default=DEFAULT_MODEL_VERSION)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--rolling-window", type=int, default=DEFAULT_ROLLING_WINDOW
    )
    parser.add_argument(
        "--n-estimators", type=int, default=DEFAULT_N_ESTIMATORS
    )
    parser.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
    args = parser.parse_args()

    result = train_rul_model(
        args.training_file,
        args.validation_file,
        args.data_metadata,
        args.output_dir,
        config=TrainingConfig(
            model_version=args.model_version,
            seed=args.seed,
            rolling_window=args.rolling_window,
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
        ),
    )
    print(
        json.dumps(
            {
                "artifact_dir": str(result.artifact_dir),
                "model_path": str(result.model_path),
                "metadata_path": str(result.metadata_path),
                "metrics": result.metrics,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
