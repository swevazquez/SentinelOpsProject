from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from services.ml.prediction_store import CsvPredictionRepository
from services.simulator.telemetry import load_asset_profiles
from services.workflows.status import (
    get_workflow_status,
    list_workflow_statuses,
    summarize_workflow_statuses,
)


@dataclass(frozen=True)
class ApiResponse:
    status_code: int
    body: dict[str, Any]


def ok(data: dict[str, Any]) -> ApiResponse:
    return ApiResponse(status_code=200, body={"status": "ok", "data": data})


def not_found(message: str) -> ApiResponse:
    return ApiResponse(
        status_code=404,
        body={"status": "not_found", "message": message},
    )


def validation_error(message: str) -> ApiResponse:
    return ApiResponse(
        status_code=400,
        body={"status": "error", "message": message},
    )


def health_response() -> ApiResponse:
    return ok({"service": "sentinelops-api", "healthy": True})


def list_assets_response(project_root: Path) -> ApiResponse:
    profiles = load_asset_profiles(
        project_root / "data" / "samples" / "asset_profiles.csv"
    )
    return ok(
        {
            "assets": [
                {
                    "asset_id": profile.asset_id,
                    "base_temperature_c": profile.base_temperature_c,
                    "base_vibration_mm_s": profile.base_vibration_mm_s,
                    "base_pressure_kpa": profile.base_pressure_kpa,
                    "runtime_hours": profile.runtime_hours,
                    "failure_risk": profile.failure_risk,
                }
                for profile in profiles
            ]
        }
    )


def workflow_status_response(project_root: Path, run_id: str) -> ApiResponse:
    try:
        status = get_workflow_status(project_root, run_id)
    except ValueError as exc:
        return validation_error(str(exc))

    if status is None:
        return not_found(f"workflow run not found: {run_id}")
    return ok({"workflow": asdict(status)})


def workflow_list_response(project_root: Path) -> ApiResponse:
    try:
        statuses = list_workflow_statuses(project_root)
    except ValueError as exc:
        return validation_error(str(exc))
    return ok({"workflows": [asdict(status) for status in statuses]})


def workflow_summary_response(project_root: Path) -> ApiResponse:
    try:
        summary = summarize_workflow_statuses(project_root)
    except ValueError as exc:
        return validation_error(str(exc))
    return ok({"summary": asdict(summary)})


def predictions_by_run_response(project_root: Path, run_id: str) -> ApiResponse:
    try:
        predictions = CsvPredictionRepository(
            project_root / "data" / "predictions"
        ).get_by_run(run_id)
    except ValueError as exc:
        return validation_error(str(exc))

    if not predictions:
        return not_found(f"predictions not found for workflow run: {run_id}")
    return ok({"predictions": predictions})


def predictions_by_asset_response(project_root: Path, asset_id: str) -> ApiResponse:
    try:
        predictions = CsvPredictionRepository(
            project_root / "data" / "predictions"
        ).get_by_asset(asset_id)
    except ValueError as exc:
        return validation_error(str(exc))

    if not predictions:
        return not_found(f"predictions not found for asset: {asset_id}")
    return ok({"predictions": predictions})
