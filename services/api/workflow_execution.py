from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from services.api.rul_demo import (
    complete_rul_demo_run,
    release_rul_demo_run,
    reserve_rul_demo_batch,
)
from services.ml.prediction_store import CsvPredictionRepository
from services.ml.rul_inference import score_rul_trajectory_file
from services.ml.rul_training import DEFAULT_MODEL_VERSION, SEMANTIC_VERSION_PATTERN
from services.ml.scoring import score_feature_file
from services.workflows.sprint1 import DEFAULT_START_TIME, run_sprint1_workflow
from services.workflows.status import record_workflow_status


@dataclass(frozen=True)
class PredictiveWorkflowResult:
    run_id: str
    raw_row_count: int
    feature_row_count: int
    prediction_row_count: int


def run_predictive_workflow(
    *,
    project_root: Path,
    run_id: str,
    start_time: datetime = DEFAULT_START_TIME,
    hours: int = 24,
    seed: int = 42,
    inference_mode: Literal["baseline", "rul"] = "rul",
    model_version: str = DEFAULT_MODEL_VERSION,
    rul_trajectory_path: Path | None = None,
) -> PredictiveWorkflowResult:
    if not SEMANTIC_VERSION_PATTERN.fullmatch(model_version):
        raise ValueError("model_version must use semantic MAJOR.MINOR.PATCH format")
    current_step = "load_predictive_inputs"
    demo_run_reserved = inference_mode == "rul" and rul_trajectory_path is not None
    try:
        if inference_mode == "baseline":
            current_step = "telemetry_and_feature_processing"
            workflow_result = run_sprint1_workflow(
                project_root=project_root,
                run_id=run_id,
                start_time=start_time,
                hours=hours,
                seed=seed,
            )
            raw_row_count = workflow_result.raw_row_count
            feature_row_count = workflow_result.feature_row_count
            current_step = "score_and_persist_predictions"
            record_workflow_status(
                project_root=project_root,
                run_id=run_id,
                status="running",
                step=current_step,
            )
            predictions = score_feature_file(workflow_result.feature_path)
        elif inference_mode == "rul":
            if rul_trajectory_path is None:
                current_step = "simulate_rul_demo_telemetry"
                batch = reserve_rul_demo_batch(project_root, run_id)
                rul_trajectory_path = batch.trajectory_path
                demo_run_reserved = True
            current_step = "rul_inference_and_persistence"
            record_workflow_status(
                project_root=project_root,
                run_id=run_id,
                status="running",
                step=current_step,
            )
            inference_result = score_rul_trajectory_file(
                rul_trajectory_path,
                project_root
                / "data"
                / "models"
                / "rul-random-forest"
                / model_version,
                run_id=run_id,
            )
            predictions = inference_result.predictions
            raw_row_count = inference_result.trajectory_row_count
            feature_row_count = inference_result.trajectory_row_count
        else:
            raise ValueError(f"unsupported inference mode: {inference_mode}")

        storage_result = CsvPredictionRepository(
            project_root / "data" / "predictions"
        ).save(predictions)
        if demo_run_reserved:
            complete_rul_demo_run(project_root, run_id)
    except Exception as exc:
        if demo_run_reserved:
            release_rul_demo_run(project_root, run_id)
        record_workflow_status(
            project_root=project_root,
            run_id=run_id,
            status="failed",
            step=current_step,
            error=str(exc),
        )
        raise

    record_workflow_status(
        project_root=project_root,
        run_id=run_id,
        status="completed",
    )
    return PredictiveWorkflowResult(
        run_id=run_id,
        raw_row_count=raw_row_count,
        feature_row_count=feature_row_count,
        prediction_row_count=storage_result.row_count,
    )
