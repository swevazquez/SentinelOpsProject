from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

import joblib

from services.ml.cmapss import (
    CONTRACT_VERSION,
    DATASET_ID,
    DEFAULT_RUL_CAP,
    RAW_FIELDS,
    SENSOR_FIELDS,
    SETTING_FIELDS,
    file_sha256,
)
from services.ml.rul_training import (
    ARTIFACT_SCHEMA_VERSION,
    MODEL_TYPE,
    SEMANTIC_VERSION_PATTERN,
    NumericRow,
    TemporalFeatureContract,
    build_temporal_feature_values,
)
from services.ml.scoring import maintenance_indicators


MODEL_NAME = "sentinelops-rul-random-forest"


@dataclass(frozen=True)
class RulArtifact:
    model: Any
    model_version: str
    model_sha256: str
    dataset_id: str
    feature_contract_version: str
    feature_contract: TemporalFeatureContract


@dataclass(frozen=True)
class RulInferenceResult:
    predictions: list[dict[str, str]]
    trajectory_row_count: int


def _require_mapping(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"RUL artifact {name} must be an object")
    return value


def _expected_feature_names(
    selected_sensor_fields: tuple[str, ...],
    rolling_window: int,
) -> tuple[str, ...]:
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
    return tuple(feature_names)


def load_rul_artifact(artifact_dir: Path) -> RulArtifact:
    metadata_path = artifact_dir / "metadata.json"
    if not metadata_path.is_file():
        raise ValueError(f"RUL artifact metadata does not exist: {metadata_path}")
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise ValueError(
            f"RUL artifact metadata is not valid JSON: {metadata_path}"
        ) from error
    metadata = _require_mapping(metadata, "metadata")

    if metadata.get("artifact_schema_version") != ARTIFACT_SCHEMA_VERSION:
        raise ValueError("RUL artifact schema version is incompatible")
    if metadata.get("model_type") != MODEL_TYPE:
        raise ValueError("RUL artifact model type is incompatible")

    model_version = metadata.get("model_version")
    if not isinstance(model_version, str) or not SEMANTIC_VERSION_PATTERN.fullmatch(
        model_version
    ):
        raise ValueError("RUL artifact model_version is invalid")
    if artifact_dir.name != model_version:
        raise ValueError("RUL artifact directory does not match model_version")

    dataset = _require_mapping(metadata.get("dataset"), "dataset")
    if dataset.get("dataset_id") != DATASET_ID:
        raise ValueError("RUL artifact dataset identifier is incompatible")
    if dataset.get("contract_version") != CONTRACT_VERSION:
        raise ValueError("RUL artifact dataset contract version is incompatible")

    preprocessing = _require_mapping(metadata.get("preprocessing"), "preprocessing")
    selected_fields_value = preprocessing.get("selected_sensor_fields")
    feature_names_value = preprocessing.get("feature_names")
    rolling_window = preprocessing.get("rolling_window")
    if (
        not isinstance(selected_fields_value, list)
        or not selected_fields_value
        or len(selected_fields_value) != len(set(selected_fields_value))
        or any(field not in SENSOR_FIELDS for field in selected_fields_value)
    ):
        raise ValueError("RUL artifact selected sensor fields are incompatible")
    if not isinstance(rolling_window, int) or rolling_window < 2:
        raise ValueError("RUL artifact rolling window is invalid")

    selected_sensor_fields = tuple(selected_fields_value)
    expected_feature_names = _expected_feature_names(
        selected_sensor_fields,
        rolling_window,
    )
    if feature_names_value != list(expected_feature_names):
        raise ValueError("RUL artifact feature contract is incompatible")

    files = _require_mapping(metadata.get("files"), "files")
    model_file = _require_mapping(files.get("model"), "model file")
    if model_file.get("path") != "model.joblib":
        raise ValueError("RUL artifact model path is incompatible")
    expected_model_sha256 = model_file.get("sha256")
    model_path = artifact_dir / "model.joblib"
    if not model_path.is_file():
        raise ValueError(f"RUL model file does not exist: {model_path}")
    actual_model_sha256 = file_sha256(model_path)
    if expected_model_sha256 != actual_model_sha256:
        raise ValueError("RUL model checksum does not match artifact metadata")

    try:
        payload = joblib.load(model_path)
    except Exception as error:
        raise ValueError(f"RUL model file cannot be loaded: {model_path}") from error
    payload = _require_mapping(payload, "model payload")
    if (
        payload.get("artifact_schema_version") != ARTIFACT_SCHEMA_VERSION
        or payload.get("model_version") != model_version
        or tuple(payload.get("feature_names", ())) != expected_feature_names
        or tuple(payload.get("selected_sensor_fields", ()))
        != selected_sensor_fields
        or payload.get("rolling_window") != rolling_window
    ):
        raise ValueError("RUL model payload does not match artifact metadata")

    model = payload.get("model")
    if not callable(getattr(model, "predict", None)):
        raise ValueError("RUL model payload does not provide prediction")
    if getattr(model, "n_features_in_", None) != len(expected_feature_names):
        raise ValueError("RUL model feature count is incompatible")

    return RulArtifact(
        model=model,
        model_version=model_version,
        model_sha256=actual_model_sha256,
        dataset_id=DATASET_ID,
        feature_contract_version=ARTIFACT_SCHEMA_VERSION,
        feature_contract=TemporalFeatureContract(
            selected_sensor_fields=selected_sensor_fields,
            dropped_sensor_fields=tuple(
                field for field in SENSOR_FIELDS if field not in selected_sensor_fields
            ),
            sensor_variances={},
            feature_names=expected_feature_names,
            rolling_window=rolling_window,
        ),
    )


def load_trajectory_rows(path: Path) -> list[NumericRow]:
    if not path.is_file():
        raise ValueError(f"C-MAPSS trajectory does not exist: {path}")

    rows: list[NumericRow] = []
    observed_keys: set[tuple[int, int]] = set()
    with path.open(newline="", encoding="utf-8") as input_file:
        reader = csv.DictReader(input_file)
        fieldnames = set(reader.fieldnames or ())
        missing_fields = [field for field in RAW_FIELDS if field not in fieldnames]
        if missing_fields:
            raise ValueError(
                "C-MAPSS trajectory is missing required fields: "
                + ", ".join(missing_fields)
            )
        for line_number, raw_row in enumerate(reader, start=2):
            row: NumericRow = {}
            for field in RAW_FIELDS:
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

            for identifier in ("engine_id", "cycle"):
                numeric_value = float(row[identifier])
                if not numeric_value.is_integer() or numeric_value < 1:
                    raise ValueError(
                        f"{path}:{line_number} field {identifier} "
                        "must be a positive integer"
                    )
                row[identifier] = int(numeric_value)

            key = (int(row["engine_id"]), int(row["cycle"]))
            if key in observed_keys:
                raise ValueError(
                    f"{path}:{line_number} duplicates engine {key[0]} cycle {key[1]}"
                )
            observed_keys.add(key)
            rows.append(row)

    if not rows:
        raise ValueError("C-MAPSS trajectory must contain at least one row")

    cycles_by_engine: dict[int, list[int]] = {}
    for row in rows:
        cycles_by_engine.setdefault(int(row["engine_id"]), []).append(
            int(row["cycle"])
        )
    for engine_id, cycles in cycles_by_engine.items():
        if sorted(cycles) != list(range(1, max(cycles) + 1)):
            raise ValueError(
                f"C-MAPSS trajectory engine {engine_id} cycles must be "
                "contiguous and begin at 1"
            )
    return sorted(rows, key=lambda row: (int(row["engine_id"]), int(row["cycle"])))


def rul_maintenance_indicators(
    remaining_useful_life_cycles: float,
) -> dict[str, str]:
    bounded_rul = max(0.0, min(float(DEFAULT_RUL_CAP), remaining_useful_life_cycles))
    health_score = bounded_rul / DEFAULT_RUL_CAP
    risk_score = 1.0 - health_score
    return {
        "risk_score": f"{risk_score:.4f}",
        "health_score": f"{health_score:.4f}",
        **maintenance_indicators(risk_score),
    }


def score_rul_trajectory_file(
    trajectory_path: Path,
    artifact_dir: Path,
    *,
    run_id: str,
    scored_at: datetime | None = None,
) -> RulInferenceResult:
    artifact = load_rul_artifact(artifact_dir)
    rows = load_trajectory_rows(trajectory_path)
    matrix = build_temporal_feature_values(rows, artifact.feature_contract)
    raw_predictions = artifact.model.predict(matrix.values)
    if len(raw_predictions) != len(matrix.values):
        raise ValueError("RUL model returned an incompatible prediction count")

    latest_index_by_engine: dict[int, int] = {}
    for index, (engine_id, cycle) in enumerate(
        zip(matrix.engine_ids, matrix.cycles, strict=True)
    ):
        current_index = latest_index_by_engine.get(engine_id)
        if current_index is None or cycle > matrix.cycles[current_index]:
            latest_index_by_engine[engine_id] = index

    scoring_time = (scored_at or datetime.now(UTC)).astimezone(UTC)
    scored_at_value = scoring_time.isoformat().replace("+00:00", "Z")
    source_sha256 = file_sha256(trajectory_path)
    predictions: list[dict[str, str]] = []
    for engine_id in sorted(latest_index_by_engine):
        index = latest_index_by_engine[engine_id]
        predicted_rul = float(raw_predictions[index])
        if not math.isfinite(predicted_rul):
            raise ValueError(f"RUL model returned a non-finite result for engine {engine_id}")
        bounded_rul = max(0.0, min(float(DEFAULT_RUL_CAP), predicted_rul))
        predictions.append(
            {
                "run_id": run_id,
                "asset_id": f"FD001-ENGINE-{engine_id:03d}",
                "prediction_type": "rul",
                "model_name": MODEL_NAME,
                "model_version": artifact.model_version,
                "scored_at": scored_at_value,
                "source_feature_path": trajectory_path.as_posix(),
                "source_feature_sha256": source_sha256,
                "model_artifact_sha256": artifact.model_sha256,
                "dataset_id": artifact.dataset_id,
                "feature_contract_version": artifact.feature_contract_version,
                "remaining_useful_life_cycles": f"{bounded_rul:.2f}",
                **rul_maintenance_indicators(bounded_rul),
            }
        )
    return RulInferenceResult(
        predictions=predictions,
        trajectory_row_count=len(rows),
    )
