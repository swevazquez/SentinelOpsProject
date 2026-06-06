from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from services.simulator.telemetry import (
    RawTelemetryStorageResult,
    generate_telemetry,
    load_asset_profiles,
    persist_raw_telemetry,
)
from services.spark_jobs.features import (
    FeatureStorageResult,
    engineer_features,
    persist_feature_rows,
)


DEFAULT_START_TIME = datetime(2026, 5, 17, tzinfo=UTC)


@dataclass(frozen=True)
class Sprint1WorkflowResult:
    run_id: str
    raw_path: Path
    raw_row_count: int
    feature_path: Path
    feature_row_count: int


def generate_and_persist_raw(
    *,
    project_root: Path,
    run_id: str,
    start_time: datetime = DEFAULT_START_TIME,
    hours: int = 24,
    seed: int = 42,
) -> RawTelemetryStorageResult:
    asset_config = project_root / "data" / "samples" / "asset_profiles.csv"
    rows = generate_telemetry(
        run_id=run_id,
        start_time=start_time,
        hours=hours,
        seed=seed,
        assets=load_asset_profiles(asset_config),
    )
    return persist_raw_telemetry(rows, project_root / "data" / "raw")


def engineer_and_persist_features(
    *,
    project_root: Path,
    raw_path: Path,
) -> FeatureStorageResult:
    rows = engineer_features(raw_path)
    return persist_feature_rows(rows, project_root / "data" / "processed")


def run_sprint1_workflow(
    *,
    project_root: Path,
    run_id: str,
    start_time: datetime = DEFAULT_START_TIME,
    hours: int = 24,
    seed: int = 42,
) -> Sprint1WorkflowResult:
    raw_result = generate_and_persist_raw(
        project_root=project_root,
        run_id=run_id,
        start_time=start_time,
        hours=hours,
        seed=seed,
    )
    feature_result = engineer_and_persist_features(
        project_root=project_root,
        raw_path=raw_result.path,
    )

    if feature_result.run_id != raw_result.run_id:
        raise ValueError(
            "processed features must preserve the raw telemetry workflow run_id"
        )

    return Sprint1WorkflowResult(
        run_id=raw_result.run_id,
        raw_path=raw_result.path,
        raw_row_count=raw_result.row_count,
        feature_path=feature_result.path,
        feature_row_count=feature_result.row_count,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Sprint 1 telemetry and feature-engineering workflow."
    )
    parser.add_argument("--run-id", default="local-run")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    result = run_sprint1_workflow(
        project_root=project_root,
        run_id=args.run_id,
        hours=args.hours,
        seed=args.seed,
    )
    raw_path = result.raw_path.relative_to(project_root)
    feature_path = result.feature_path.relative_to(project_root)
    print(f"Sprint 1 workflow completed for run {result.run_id}:")
    print(f"  raw telemetry: {raw_path} ({result.raw_row_count} rows)")
    print(f"  processed features: {feature_path} ({result.feature_row_count} rows)")


if __name__ == "__main__":
    main()
