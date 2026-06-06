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
        from services.workflows.sprint1 import generate_and_persist_raw

        run_id = datetime.now(UTC).strftime("airflow-%Y%m%dT%H%M%SZ")
        result = generate_and_persist_raw(
            project_root=PROJECT_ROOT,
            run_id=run_id,
            start_time=datetime(2026, 5, 17, tzinfo=UTC),
            hours=24,
        )
        return str(result.path)

    @task
    def engineer_feature_output(raw_path: str) -> str:
        from services.workflows.sprint1 import engineer_and_persist_features

        result = engineer_and_persist_features(
            project_root=PROJECT_ROOT,
            raw_path=Path(raw_path),
        )
        return str(result.path)

    engineer_feature_output(generate_raw_telemetry())


sentinelops_sprint1_pipeline()
