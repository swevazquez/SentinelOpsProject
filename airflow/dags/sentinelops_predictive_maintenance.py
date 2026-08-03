from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from airflow.decorators import dag, task


PROJECT_ROOT = Path(os.environ.get("SENTINELOPS_PROJECT_ROOT", "/opt/airflow"))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _airflow_run_id() -> str:
    from airflow.operators.python import get_current_context

    context = get_current_context()
    dag_run = context.get("dag_run")
    return getattr(dag_run, "run_id", None) or "unknown-airflow-run"


def _airflow_run_model_version() -> str | None:
    from airflow.operators.python import get_current_context

    context = get_current_context()
    dag_run = context.get("dag_run")
    configuration = getattr(dag_run, "conf", None) or {}
    model_version = configuration.get("model_version")
    return model_version if isinstance(model_version, str) and model_version else None


def report_workflow_failure(context: dict[str, Any]) -> None:
    from services.workflows.airflow_pipeline import report_airflow_failure

    report_airflow_failure(context, project_root=PROJECT_ROOT)


@dag(
    dag_id="sentinelops_predictive_maintenance",
    description=(
        "Final RUL workflow: select a repeatable input, run Spark batch scoring, "
        "persist results, and report workflow status."
    ),
    start_date=datetime(2026, 5, 17, tzinfo=UTC),
    schedule=None,
    catchup=False,
    tags=["sentinelops", "predictive-maintenance", "rul"],
    on_failure_callback=report_workflow_failure,
)
def sentinelops_predictive_maintenance():
    @task(task_id="select_predictive_input")
    def select_input() -> dict[str, object]:
        from services.workflows.airflow_pipeline import select_predictive_input

        return select_predictive_input(
            project_root=PROJECT_ROOT,
            run_id=_airflow_run_id(),
            model_version=_airflow_run_model_version(),
        )

    @task(task_id="run_spark_rul_batch")
    def run_spark_batch(selection: dict[str, object]) -> dict[str, object]:
        from services.workflows.airflow_pipeline import execute_predictive_batch

        return execute_predictive_batch(
            project_root=PROJECT_ROOT,
            selection=selection,
        )

    @task(task_id="finalize_predictive_workflow")
    def finalize_workflow(
        selection: dict[str, object],
        batch_result: dict[str, object],
    ) -> dict[str, object]:
        from services.workflows.airflow_pipeline import finalize_predictive_workflow

        return finalize_predictive_workflow(
            project_root=PROJECT_ROOT,
            selection=selection,
            batch_result=batch_result,
        )

    selected_input = select_input()
    batch_result = run_spark_batch(selected_input)
    finalize_workflow(selected_input, batch_result)


sentinelops_predictive_maintenance()
