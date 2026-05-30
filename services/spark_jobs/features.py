from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


DEFAULT_PROCESSED_STORAGE_DIR = Path("data/processed")
REQUIRED_RAW_FIELDS = [
    "run_id",
    "asset_id",
    "timestamp",
    "temperature_c",
    "vibration_mm_s",
    "pressure_kpa",
    "runtime_hours",
    "failure_within_7d",
]

FEATURE_FIELDS = [
    "run_id",
    "asset_id",
    "sample_count",
    "first_timestamp",
    "last_timestamp",
    "avg_temperature_c",
    "max_temperature_c",
    "avg_vibration_mm_s",
    "max_vibration_mm_s",
    "avg_pressure_kpa",
    "min_runtime_hours",
    "max_runtime_hours",
    "failure_observed",
]


@dataclass(frozen=True)
class FeatureStorageResult:
    path: Path
    run_id: str
    row_count: int


def _validate_raw_reader(reader: csv.DictReader) -> None:
    missing_fields = [
        field
        for field in REQUIRED_RAW_FIELDS
        if field not in (reader.fieldnames or [])
    ]
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"raw telemetry missing required fields: {missing}")


def _validate_raw_row(row: dict[str, str], row_number: int) -> None:
    empty_fields = [
        field
        for field in REQUIRED_RAW_FIELDS
        if row.get(field, "") == ""
    ]
    if empty_fields:
        missing = ", ".join(sorted(empty_fields))
        raise ValueError(f"raw telemetry row {row_number} missing values: {missing}")


def engineer_features(input_path: Path) -> list[dict[str, str]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)

    with input_path.open(newline="", encoding="utf-8") as input_file:
        reader = csv.DictReader(input_file)
        _validate_raw_reader(reader)
        for row_number, row in enumerate(reader, start=2):
            _validate_raw_row(row, row_number)
            groups[(row["run_id"], row["asset_id"])].append(row)

    if not groups:
        raise ValueError("raw telemetry input must include at least one row")

    features: list[dict[str, str]] = []
    for (run_id, asset_id), rows in sorted(groups.items()):
        temperatures = [float(row["temperature_c"]) for row in rows]
        vibrations = [float(row["vibration_mm_s"]) for row in rows]
        pressures = [float(row["pressure_kpa"]) for row in rows]
        runtimes = [int(row["runtime_hours"]) for row in rows]
        failures = [int(row["failure_within_7d"]) for row in rows]
        timestamps = [row["timestamp"] for row in rows]

        features.append(
            {
                "run_id": run_id,
                "asset_id": asset_id,
                "sample_count": str(len(rows)),
                "first_timestamp": min(timestamps),
                "last_timestamp": max(timestamps),
                "avg_temperature_c": f"{sum(temperatures) / len(temperatures):.2f}",
                "max_temperature_c": f"{max(temperatures):.2f}",
                "avg_vibration_mm_s": f"{sum(vibrations) / len(vibrations):.2f}",
                "max_vibration_mm_s": f"{max(vibrations):.2f}",
                "avg_pressure_kpa": f"{sum(pressures) / len(pressures):.2f}",
                "min_runtime_hours": str(min(runtimes)),
                "max_runtime_hours": str(max(runtimes)),
                "failure_observed": str(max(failures)),
            }
        )

    return features


def _validate_feature_rows(rows: list[dict[str, str]]) -> str:
    if not rows:
        raise ValueError("feature storage requires at least one row")

    run_ids = {row.get("run_id", "") for row in rows}
    if len(run_ids) != 1 or "" in run_ids:
        raise ValueError("feature rows must contain exactly one non-empty run_id")

    missing_fields = [
        field
        for field in FEATURE_FIELDS
        if any(field not in row or row[field] == "" for row in rows)
    ]
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"feature rows missing required fields: {missing}")

    return next(iter(run_ids))


def write_features_csv(rows: list[dict[str, str]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=FEATURE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def persist_feature_rows(
    rows: list[dict[str, str]],
    storage_dir: Path = DEFAULT_PROCESSED_STORAGE_DIR,
) -> FeatureStorageResult:
    run_id = _validate_feature_rows(rows)
    output_path = storage_dir / f"features_{run_id}.csv"
    path = write_features_csv(rows, output_path)
    return FeatureStorageResult(path=path, run_id=run_id, row_count=len(rows))


def main() -> None:
    parser = argparse.ArgumentParser(description="Create Sprint 1 feature CSV data.")
    parser.add_argument("--input", required=True, help="Raw telemetry CSV path.")
    parser.add_argument("--output", help="Explicit processed feature CSV path.")
    parser.add_argument(
        "--processed-dir",
        default=str(DEFAULT_PROCESSED_STORAGE_DIR),
        help="Processed feature storage directory used when --output is omitted.",
    )
    args = parser.parse_args()

    rows = engineer_features(Path(args.input))
    if args.output:
        _validate_feature_rows(rows)
        path = write_features_csv(rows, Path(args.output))
        print(f"Generated {len(rows)} feature rows at {path}")
        return

    result = persist_feature_rows(rows, Path(args.processed_dir))
    print(f"Persisted {result.row_count} feature rows at {result.path}")


if __name__ == "__main__":
    main()
