from __future__ import annotations

import argparse
import csv
import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path


DEFAULT_ASSET_CONFIG_PATH = Path("data/samples/asset_profiles.csv")

TELEMETRY_FIELDS = [
    "run_id",
    "asset_id",
    "timestamp",
    "temperature_c",
    "vibration_mm_s",
    "pressure_kpa",
    "runtime_hours",
    "failure_within_7d",
]


@dataclass(frozen=True)
class AssetProfile:
    asset_id: str
    base_temperature_c: float
    base_vibration_mm_s: float
    base_pressure_kpa: float
    runtime_hours: int
    failure_risk: float


DEFAULT_ASSETS = [
    AssetProfile("A-100", 67.5, 2.1, 214.0, 1280, 0.08),
    AssetProfile("A-101", 78.0, 3.8, 236.0, 2140, 0.32),
    AssetProfile("A-102", 72.0, 2.9, 225.0, 1730, 0.18),
    AssetProfile("A-103", 84.0, 5.2, 248.0, 2675, 0.58),
]


def load_asset_profiles(config_path: Path) -> list[AssetProfile]:
    if not config_path.exists():
        raise FileNotFoundError(f"asset configuration not found: {config_path}")

    with config_path.open(newline="", encoding="utf-8") as config_file:
        reader = csv.DictReader(config_file)
        required_fields = {
            "asset_id",
            "base_temperature_c",
            "base_vibration_mm_s",
            "base_pressure_kpa",
            "runtime_hours",
            "failure_risk",
        }
        missing_fields = required_fields.difference(reader.fieldnames or [])
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"asset configuration missing fields: {missing}")

        profiles = [
            AssetProfile(
                asset_id=row["asset_id"],
                base_temperature_c=float(row["base_temperature_c"]),
                base_vibration_mm_s=float(row["base_vibration_mm_s"]),
                base_pressure_kpa=float(row["base_pressure_kpa"]),
                runtime_hours=int(row["runtime_hours"]),
                failure_risk=float(row["failure_risk"]),
            )
            for row in reader
        ]

    if not profiles:
        raise ValueError("asset configuration must include at least one asset")

    invalid_risks = [
        profile.asset_id
        for profile in profiles
        if profile.failure_risk < 0 or profile.failure_risk > 1
    ]
    if invalid_risks:
        assets = ", ".join(invalid_risks)
        raise ValueError(f"failure_risk must be between 0 and 1 for assets: {assets}")

    return profiles


def generate_telemetry(
    *,
    run_id: str,
    start_time: datetime,
    hours: int = 24,
    seed: int = 42,
    assets: list[AssetProfile] | None = None,
) -> list[dict[str, str]]:
    if hours <= 0:
        raise ValueError("hours must be greater than zero")

    rng = random.Random(seed)
    rows: list[dict[str, str]] = []
    selected_assets = assets or DEFAULT_ASSETS

    for hour in range(hours):
        timestamp = (start_time + timedelta(hours=hour)).astimezone(UTC)
        for asset in selected_assets:
            temperature = asset.base_temperature_c + rng.uniform(-2.5, 4.5)
            vibration = asset.base_vibration_mm_s + rng.uniform(-0.35, 0.8)
            pressure = asset.base_pressure_kpa + rng.uniform(-5.0, 8.0)
            runtime = asset.runtime_hours + hour
            failure = 1 if rng.random() < asset.failure_risk else 0

            rows.append(
                {
                    "run_id": run_id,
                    "asset_id": asset.asset_id,
                    "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
                    "temperature_c": f"{temperature:.2f}",
                    "vibration_mm_s": f"{vibration:.2f}",
                    "pressure_kpa": f"{pressure:.2f}",
                    "runtime_hours": str(runtime),
                    "failure_within_7d": str(failure),
                }
            )

    return rows


def write_telemetry_csv(rows: list[dict[str, str]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=TELEMETRY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def parse_utc_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SentinelOps telemetry CSV data.")
    parser.add_argument("--output", required=True, help="Destination CSV path.")
    parser.add_argument("--run-id", default="local-run", help="Workflow or generation run identifier.")
    parser.add_argument("--hours", type=int, default=24, help="Number of hourly samples per asset.")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed.")
    parser.add_argument(
        "--asset-config",
        default=str(DEFAULT_ASSET_CONFIG_PATH),
        help="CSV file containing representative asset profiles.",
    )
    parser.add_argument(
        "--start-time",
        default="2026-05-17T00:00:00Z",
        help="UTC ISO timestamp for the first sample.",
    )
    args = parser.parse_args()

    rows = generate_telemetry(
        run_id=args.run_id,
        start_time=parse_utc_datetime(args.start_time),
        hours=args.hours,
        seed=args.seed,
        assets=load_asset_profiles(Path(args.asset_config)),
    )
    path = write_telemetry_csv(rows, Path(args.output))
    print(f"Generated {len(rows)} telemetry rows at {path}")


if __name__ == "__main__":
    main()
