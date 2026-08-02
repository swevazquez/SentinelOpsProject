from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Mapping

from services.api.rul_demo import (
    complete_rul_demo_run,
    release_rul_demo_run,
    reserve_rul_demo_batch,
)
from services.spark_jobs.rul_batch import (
    DEFAULT_SPARK_MASTER,
    DEFAULT_MODEL_VERSION,
    SEMANTIC_VERSION_PATTERN,
    SparkRulBatchConfig,
    run_spark_rul_batch,
)
from services.workflows.status import record_workflow_status


AIRFLOW_INPUT_PATH_ENV = "SENTINELOPS_AIRFLOW_INPUT_PATH"
AIRFLOW_MODEL_VERSION_ENV = "SENTINELOPS_AIRFLOW_MODEL_VERSION"
SPARK_MASTER_ENV = "SPARK_MASTER_URL"


@dataclass(frozen=True)
class AirflowInputSelection:
    run_id: str
    input_path: str
    model_version: str
    demo_reserved: bool
    checkpoint_number: int | None = None
    checkpoint_label: str | None = None

    def as_payload(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "input_path": self.input_path,
            "model_version": self.model_version,
            "demo_reserved": self.demo_reserved,
            "checkpoint_number": self.checkpoint_number,
            "checkpoint_label": self.checkpoint_label,
        }


def select_predictive_input(
    *,
    project_root: Path,
    run_id: str,
    model_version: str | None = None,
    input_path: Path | str | None = None,
) -> dict[str, object]:
    """Select a repeatable RUL demo checkpoint or an explicitly configured input."""
    _validate_run_id(run_id)
    resolved_model_version = model_version or os.getenv(
        AIRFLOW_MODEL_VERSION_ENV,
        DEFAULT_MODEL_VERSION,
    )
    _validate_model_version(resolved_model_version)

    root = project_root.resolve()
    configured_input = input_path
    if configured_input is None:
        configured_value = os.getenv(AIRFLOW_INPUT_PATH_ENV, "").strip()
        configured_input = configured_value or None

    demo_reserved = False
    try:
        if configured_input is None:
            batch = reserve_rul_demo_batch(root, run_id)
            demo_reserved = True
            selection = AirflowInputSelection(
                run_id=run_id,
                input_path=_portable_path(batch.trajectory_path, root),
                model_version=resolved_model_version,
                demo_reserved=True,
                checkpoint_number=batch.checkpoint_index + 1,
                checkpoint_label=batch.checkpoint_label,
            )
        else:
            resolved_input = _resolve_path(root, configured_input)
            if not resolved_input.is_file():
                raise ValueError(
                    f"configured Airflow RUL input does not exist: {resolved_input}"
                )
            selection = AirflowInputSelection(
                run_id=run_id,
                input_path=_portable_path(resolved_input, root),
                model_version=resolved_model_version,
                demo_reserved=False,
            )

        record_workflow_status(
            project_root=root,
            run_id=run_id,
            status="running",
            step="airflow_input_selection",
        )
        return selection.as_payload()
    except Exception as error:
        if demo_reserved:
            release_rul_demo_run(root, run_id)
        _record_failure(
            project_root=root,
            run_id=run_id,
            step="airflow_input_selection",
            error=error,
        )
        raise


def execute_predictive_batch(
    *,
    project_root: Path,
    selection: Mapping[str, object],
    spark_master: str | None = None,
    spark_session: Any | None = None,
) -> dict[str, object]:
    """Invoke the shared Spark boundary without duplicating ML or persistence logic."""
    validated = _selection_from_payload(selection)
    root = project_root.resolve()
    input_path = _resolve_path(root, validated.input_path)
    master = spark_master or os.getenv(SPARK_MASTER_ENV, DEFAULT_SPARK_MASTER)
    try:
        result = run_spark_rul_batch(
            SparkRulBatchConfig(
                project_root=root,
                input_path=input_path,
                run_id=validated.run_id,
                model_version=validated.model_version,
                master=master,
            ),
            spark_session=spark_session,
        )
    except Exception:
        if validated.demo_reserved:
            release_rul_demo_run(root, validated.run_id)
        raise

    return {
        "run_id": result.run_id,
        "input_row_count": result.input_row_count,
        "prediction_row_count": result.prediction_row_count,
        "asset_count": result.asset_count,
        "model_version": result.model_version,
    }


def finalize_predictive_workflow(
    *,
    project_root: Path,
    selection: Mapping[str, object],
    batch_result: Mapping[str, object],
) -> dict[str, object]:
    """Advance a demo checkpoint and publish the final successful workflow state."""
    validated = _selection_from_payload(selection)
    if batch_result.get("run_id") != validated.run_id:
        raise ValueError("Airflow batch result run_id does not match input selection")

    root = project_root.resolve()
    try:
        if validated.demo_reserved:
            checkpoint = complete_rul_demo_run(root, validated.run_id)
        else:
            checkpoint = None
        record_workflow_status(
            project_root=root,
            run_id=validated.run_id,
            status="completed",
            step="airflow_workflow_complete",
        )
    except Exception as error:
        if validated.demo_reserved:
            release_rul_demo_run(root, validated.run_id)
        _record_failure(
            project_root=root,
            run_id=validated.run_id,
            step="airflow_workflow_complete",
            error=error,
        )
        raise

    return {
        "run_id": validated.run_id,
        "status": "completed",
        "checkpoint": checkpoint,
        "batch": dict(batch_result),
    }


def report_airflow_failure(context: Mapping[str, object], *, project_root: Path) -> None:
    """Release a reserved demo checkpoint and persist a sanitized DAG failure."""
    dag_run = context.get("dag_run")
    task_instance = context.get("task_instance")
    exception = context.get("exception")
    run_id = getattr(dag_run, "run_id", None) or "unknown-airflow-run"
    failed_step = getattr(task_instance, "task_id", None)
    root = project_root.resolve()
    try:
        release_rul_demo_run(root, run_id)
    except Exception:
        # A corrupted demo-state file must not prevent the failed status record.
        pass
    _record_failure(
        project_root=root,
        run_id=run_id,
        step=failed_step,
        error=exception or RuntimeError("Airflow DAG run failed"),
    )


def _selection_from_payload(payload: Mapping[str, object]) -> AirflowInputSelection:
    run_id = payload.get("run_id")
    input_path = payload.get("input_path")
    model_version = payload.get("model_version")
    demo_reserved = payload.get("demo_reserved")
    if not all(
        isinstance(value, str) and value
        for value in (run_id, input_path, model_version)
    ):
        raise ValueError("Airflow input selection has invalid required fields")
    if not isinstance(demo_reserved, bool):
        raise ValueError("Airflow input selection demo_reserved must be boolean")
    _validate_run_id(run_id)
    _validate_model_version(model_version)
    checkpoint_number = payload.get("checkpoint_number")
    if checkpoint_number is not None and (
        not isinstance(checkpoint_number, int) or checkpoint_number < 1
    ):
        raise ValueError("Airflow input selection checkpoint_number is invalid")
    checkpoint_label = payload.get("checkpoint_label")
    if checkpoint_label is not None and not isinstance(checkpoint_label, str):
        raise ValueError("Airflow input selection checkpoint_label is invalid")
    return AirflowInputSelection(
        run_id=run_id,
        input_path=input_path,
        model_version=model_version,
        demo_reserved=demo_reserved,
        checkpoint_number=checkpoint_number,
        checkpoint_label=checkpoint_label,
    )


def _resolve_path(project_root: Path, value: Path | str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_root / path


def _portable_path(path: Path, project_root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(project_root).as_posix()
    except ValueError:
        return resolved.as_posix()


def _validate_run_id(run_id: str) -> None:
    if not run_id or any(character in run_id for character in ("/", "\\", "..")):
        raise ValueError("run_id must be a non-empty file-safe value")


def _validate_model_version(model_version: str) -> None:
    if not SEMANTIC_VERSION_PATTERN.fullmatch(model_version):
        raise ValueError("model_version must use semantic MAJOR.MINOR.PATCH format")


def _record_failure(
    *,
    project_root: Path,
    run_id: str,
    step: str | None,
    error: BaseException,
) -> None:
    try:
        record_workflow_status(
            project_root=project_root,
            run_id=run_id,
            status="failed",
            step=step,
            error=_sanitized_error(error),
        )
    except Exception:
        # Preserve the original task failure if the status backend is unavailable.
        return


def _sanitized_error(error: BaseException) -> str:
    message = " ".join(str(error).split())
    if "postgresql://" in message and "@" in message:
        prefix, remainder = message.split("postgresql://", maxsplit=1)
        _, suffix = remainder.split("@", maxsplit=1)
        message = f"{prefix}postgresql://***@{suffix}"
    return f"{type(error).__name__}: {message}"[:500]
