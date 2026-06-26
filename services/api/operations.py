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


def _body(
    *,
    status: str,
    message: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "status": status,
        "message": message,
        "request_state": status,
    }
    if data is not None:
        body["data"] = data
    return body


def ok(data: dict[str, Any], message: str = "request completed") -> ApiResponse:
    return ApiResponse(
        status_code=200,
        body=_body(status="ok", message=message, data=data),
    )


def not_found(message: str) -> ApiResponse:
    return ApiResponse(
        status_code=404,
        body=_body(status="not_found", message=message),
    )


def validation_error(message: str) -> ApiResponse:
    return ApiResponse(
        status_code=400,
        body=_body(status="error", message=message),
    )


def unavailable(message: str) -> ApiResponse:
    return ApiResponse(
        status_code=503,
        body=_body(status="unavailable", message=message),
    )


def health_response() -> ApiResponse:
    return ok(
        {"service": "sentinelops-api", "healthy": True},
        "api service is healthy",
    )


def list_assets_response(project_root: Path) -> ApiResponse:
    asset_path = project_root / "data" / "samples" / "asset_profiles.csv"
    if not asset_path.exists():
        return unavailable(f"asset profile source is unavailable: {asset_path}")

    try:
        profiles = load_asset_profiles(asset_path)
    except ValueError as exc:
        return validation_error(str(exc))

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
        },
        "asset profiles retrieved",
    )


def workflow_status_response(project_root: Path, run_id: str) -> ApiResponse:
    try:
        status = get_workflow_status(project_root, run_id)
    except ValueError as exc:
        return validation_error(str(exc))

    if status is None:
        return not_found(f"workflow run not found: {run_id}")
    return ok({"workflow": asdict(status)}, "workflow status retrieved")


def workflow_list_response(project_root: Path) -> ApiResponse:
    try:
        statuses = list_workflow_statuses(project_root)
    except ValueError as exc:
        return validation_error(str(exc))
    return ok(
        {"workflows": [asdict(status) for status in statuses]},
        "workflow statuses retrieved",
    )


def workflow_summary_response(project_root: Path) -> ApiResponse:
    try:
        summary = summarize_workflow_statuses(project_root)
    except ValueError as exc:
        return validation_error(str(exc))
    return ok({"summary": asdict(summary)}, "workflow summary retrieved")


def predictions_by_run_response(project_root: Path, run_id: str) -> ApiResponse:
    try:
        predictions = CsvPredictionRepository(
            project_root / "data" / "predictions"
        ).get_by_run(run_id)
    except ValueError as exc:
        return validation_error(str(exc))

    if not predictions:
        return not_found(f"predictions not found for workflow run: {run_id}")
    return ok({"predictions": predictions}, "predictions retrieved")


def predictions_by_asset_response(project_root: Path, asset_id: str) -> ApiResponse:
    try:
        predictions = CsvPredictionRepository(
            project_root / "data" / "predictions"
        ).get_by_asset(asset_id)
    except ValueError as exc:
        return validation_error(str(exc))

    if not predictions:
        return not_found(f"predictions not found for asset: {asset_id}")
    return ok({"predictions": predictions}, "predictions retrieved")
