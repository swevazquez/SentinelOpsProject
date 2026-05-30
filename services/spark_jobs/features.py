from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


FEATURE_FIELDS = [
    "run_id",
    "asset_id",
    "sample_count",
    "avg_temperature_c",
    "max_temperature_c",
    "avg_vibration_mm_s",
    "max_vibration_mm_s",
    "avg_pressure_kpa",
    "max_runtime_hours",
    "failure_observed",
]


def engineer_features(input_path: Path) -> list[dict[str, str]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)

    with input_path.open(newline="", encoding="utf-8") as input_file:
        reader = csv.DictReader(input_file)
        for row in reader:
            groups[(row["run_id"], row["asset_id"])].append(row)

    features: list[dict[str, str]] = []
    for (run_id, asset_id), rows in sorted(groups.items()):
        temperatures = [float(row["temperature_c"]) for row in rows]
        vibrations = [float(row["vibration_mm_s"]) for row in rows]
        pressures = [float(row["pressure_kpa"]) for row in rows]
        runtimes = [int(row["runtime_hours"]) for row in rows]
        failures = [int(row["failure_within_7d"]) for row in rows]

        features.append(
            {
                "run_id": run_id,
                "asset_id": asset_id,
                "sample_count": str(len(rows)),
                "avg_temperature_c": f"{sum(temperatures) / len(temperatures):.2f}",
                "max_temperature_c": f"{max(temperatures):.2f}",
                "avg_vibration_mm_s": f"{sum(vibrations) / len(vibrations):.2f}",
                "max_vibration_mm_s": f"{max(vibrations):.2f}",
                "avg_pressure_kpa": f"{sum(pressures) / len(pressures):.2f}",
                "max_runtime_hours": str(max(runtimes)),
                "failure_observed": str(max(failures)),
            }
        )

    return features


def write_features_csv(rows: list[dict[str, str]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=FEATURE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create Sprint 1 feature CSV data.")
    parser.add_argument("--input", required=True, help="Raw telemetry CSV path.")
    parser.add_argument("--output", required=True, help="Processed feature CSV path.")
    args = parser.parse_args()

    rows = engineer_features(Path(args.input))
    path = write_features_csv(rows, Path(args.output))
    print(f"Generated {len(rows)} feature rows at {path}")


if __name__ == "__main__":
    main()
