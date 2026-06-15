from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


MODEL_NAME = "sentinelops-risk-baseline"
MODEL_VERSION = "1.0.0"

REQUIRED_FEATURE_FIELDS = [
    "run_id",
    "asset_id",
    "max_temperature_c",
    "max_vibration_mm_s",
    "avg_pressure_kpa",
    "max_runtime_hours",
    "failure_observed",
]

PREDICTION_FIELDS = [
    "run_id",
    "asset_id",
    "model_name",
    "model_version",
    "scored_at",
    "source_feature_path",
    "source_feature_sha256",
    "risk_score",
    "asset_status",
    "maintenance_priority",
    "recommended_action",
]


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _normalized(value: float, low: float, high: float) -> float:
    return _clamp((value - low) / (high - low))


def _validate_feature_rows(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("predictive scoring requires at least one feature row")

    missing_fields = [
        field
        for field in REQUIRED_FEATURE_FIELDS
        if any(field not in row or row[field] == "" for row in rows)
    ]
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"feature rows missing required scoring fields: {missing}")

    run_ids = {row["run_id"] for row in rows}
    if len(run_ids) != 1:
        raise ValueError("feature rows must contain exactly one workflow run_id")

    asset_ids = [row["asset_id"] for row in rows]
    if len(asset_ids) != len(set(asset_ids)):
        raise ValueError("feature rows must contain one row per asset")


def calculate_risk_score(feature_row: dict[str, str]) -> float:
    temperature_risk = _normalized(
        float(feature_row["max_temperature_c"]),
        65.0,
        95.0,
    )
    vibration_risk = _normalized(
        float(feature_row["max_vibration_mm_s"]),
        1.5,
        7.5,
    )
    pressure_risk = _clamp(
        abs(float(feature_row["avg_pressure_kpa"]) - 220.0) / 50.0
    )
    runtime_risk = _normalized(
        float(feature_row["max_runtime_hours"]),
        500.0,
        3500.0,
    )
    failure_risk = _clamp(float(feature_row["failure_observed"]))

    score = (
        temperature_risk * 0.25
        + vibration_risk * 0.35
        + pressure_risk * 0.10
        + runtime_risk * 0.15
        + failure_risk * 0.15
    )
    return round(_clamp(score), 4)


def maintenance_indicators(risk_score: float) -> dict[str, str]:
    if risk_score >= 0.75:
        return {
            "asset_status": "critical",
            "maintenance_priority": "immediate",
            "recommended_action": "Inspect asset and schedule immediate maintenance.",
        }
    if risk_score >= 0.50:
        return {
            "asset_status": "warning",
            "maintenance_priority": "high",
            "recommended_action": "Schedule maintenance within 24 hours.",
        }
    if risk_score >= 0.25:
        return {
            "asset_status": "watch",
            "maintenance_priority": "medium",
            "recommended_action": "Review telemetry trends during the next shift.",
        }
    return {
        "asset_status": "healthy",
        "maintenance_priority": "routine",
        "recommended_action": "Continue routine monitoring.",
    }


def _feature_rows_sha256(rows: list[dict[str, str]]) -> str:
    canonical_rows = json.dumps(
        sorted(rows, key=lambda row: row["asset_id"]),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical_rows).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def score_feature_rows(
    rows: list[dict[str, str]],
    *,
    scored_at: datetime | None = None,
    source_feature_path: str = "in-memory",
    source_feature_sha256: str | None = None,
) -> list[dict[str, str]]:
    _validate_feature_rows(rows)
    scoring_time = (scored_at or datetime.now(UTC)).astimezone(UTC)
    scored_at_value = scoring_time.isoformat().replace("+00:00", "Z")
    source_sha256 = source_feature_sha256 or _feature_rows_sha256(rows)

    predictions: list[dict[str, str]] = []
    for row in sorted(rows, key=lambda item: item["asset_id"]):
        risk_score = calculate_risk_score(row)
        predictions.append(
            {
                "run_id": row["run_id"],
                "asset_id": row["asset_id"],
                "model_name": MODEL_NAME,
                "model_version": MODEL_VERSION,
                "scored_at": scored_at_value,
                "source_feature_path": source_feature_path,
                "source_feature_sha256": source_sha256,
                "risk_score": f"{risk_score:.4f}",
                **maintenance_indicators(risk_score),
            }
        )
    return predictions


def load_feature_rows(input_path: Path) -> list[dict[str, str]]:
    with input_path.open(newline="", encoding="utf-8") as input_file:
        return list(csv.DictReader(input_file))


def score_feature_file(
    input_path: Path,
    *,
    scored_at: datetime | None = None,
) -> list[dict[str, str]]:
    rows = load_feature_rows(input_path)
    return score_feature_rows(
        rows,
        scored_at=scored_at,
        source_feature_path=input_path.as_posix(),
        source_feature_sha256=_file_sha256(input_path),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Score processed SentinelOps feature rows."
    )
    parser.add_argument("--input", required=True, help="Processed feature CSV path.")
    args = parser.parse_args()

    predictions = score_feature_file(Path(args.input))
    print(json.dumps(predictions, indent=2))


if __name__ == "__main__":
    main()
