from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from airflow.decorators import dag, task


PROJECT_ROOT = Path(os.environ.get("SENTINELOPS_PROJECT_ROOT", "/opt/airflow"))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dag(
    dag_id="sentinelops_sprint1_pipeline",
    description="Sprint 1 telemetry generation, raw storage, and feature processing workflow.",
    start_date=datetime(2026, 5, 17, tzinfo=UTC),
    schedule=None,
    catchup=False,
    tags=["sentinelops", "sprint-1"],
)
def sentinelops_sprint1_pipeline():
    @task
    def generate_raw_telemetry() -> str:
        from services.simulator.telemetry import generate_telemetry, write_telemetry_csv

        run_id = datetime.now(UTC).strftime("airflow-%Y%m%dT%H%M%SZ")
        output_path = PROJECT_ROOT / "data" / "raw" / f"telemetry_{run_id}.csv"
        rows = generate_telemetry(
            run_id=run_id,
            start_time=datetime(2026, 5, 17, tzinfo=UTC),
            hours=24,
        )
        write_telemetry_csv(rows, output_path)
        return str(output_path)

    @task
    def engineer_feature_output(raw_path: str) -> str:
        from services.spark_jobs.features import engineer_features, write_features_csv

        input_path = Path(raw_path)
        output_path = PROJECT_ROOT / "data" / "processed" / input_path.name.replace(
            "telemetry_",
            "features_",
        )
        rows = engineer_features(input_path)
        write_features_csv(rows, output_path)
        return str(output_path)

    engineer_feature_output(generate_raw_telemetry())


sentinelops_sprint1_pipeline()
