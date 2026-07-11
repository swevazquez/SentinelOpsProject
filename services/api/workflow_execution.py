from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from services.ml.prediction_store import CsvPredictionRepository
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
) -> PredictiveWorkflowResult:
    current_step = "telemetry_and_feature_processing"
    try:
        workflow_result = run_sprint1_workflow(
            project_root=project_root,
            run_id=run_id,
            start_time=start_time,
            hours=hours,
            seed=seed,
        )
        current_step = "score_and_persist_predictions"
        record_workflow_status(
            project_root=project_root,
            run_id=run_id,
            status="running",
            step=current_step,
        )
        predictions = score_feature_file(workflow_result.feature_path)
        storage_result = CsvPredictionRepository(
            project_root / "data" / "predictions"
        ).save(predictions)
    except Exception as exc:
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
        raw_row_count=workflow_result.raw_row_count,
        feature_row_count=workflow_result.feature_row_count,
        prediction_row_count=storage_result.row_count,
    )
