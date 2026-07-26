from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from services.api.rul_demo import (
    SCENARIO_PATH,
    configured_rul_demo_asset_ids,
    current_rul_demo_run_ids,
)
from services.ml.prediction_store import CsvPredictionRepository
from services.simulator.telemetry import load_asset_profiles
from services.workflows.status import (
    WorkflowStatus,
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


def _prediction_result_summary(
    predictions: list[dict[str, str]],
) -> dict[str, Any] | None:
    if not predictions:
        return None
    counts = {
        status: sum(
            prediction["asset_status"] == status
            for prediction in predictions
        )
        for status in ("critical", "warning", "watch", "healthy")
    }
    outcome_status = next(
        (
            status
            for status in ("critical", "warning", "watch")
            if counts[status]
        ),
        "healthy",
    )
    rul_values = [
        float(prediction["remaining_useful_life_cycles"])
        for prediction in predictions
        if prediction.get("remaining_useful_life_cycles")
    ]
    return {
        "asset_count": len(predictions),
        **counts,
        "finding_count": counts["critical"] + counts["warning"] + counts["watch"],
        "outcome_status": outcome_status,
        "outcome_label": (
            "No active findings"
            if outcome_status == "healthy"
            else f"{outcome_status.title()} findings"
        ),
        "shortest_rul_cycles": min(rul_values) if rul_values else None,
        "highest_risk_score": max(
            float(prediction["risk_score"])
            for prediction in predictions
        ),
    }


def _workflow_payload(
    project_root: Path,
    workflow: WorkflowStatus,
) -> dict[str, Any]:
    payload = asdict(workflow)
    payload["result_summary"] = None
    if payload["status"] == "completed":
        predictions = CsvPredictionRepository(
            project_root / "data" / "predictions"
        ).get_by_run(payload["run_id"])
        payload["result_summary"] = _prediction_result_summary(predictions)
    return payload


def workflow_status_response(project_root: Path, run_id: str) -> ApiResponse:
    try:
        status = get_workflow_status(project_root, run_id)
    except ValueError as exc:
        return validation_error(str(exc))

    if status is None:
        return not_found(f"workflow run not found: {run_id}")
    try:
        workflow = _workflow_payload(project_root, status)
    except ValueError as exc:
        return validation_error(str(exc))
    return ok({"workflow": workflow}, "workflow status retrieved")


def workflow_list_response(project_root: Path) -> ApiResponse:
    try:
        statuses = list_workflow_statuses(project_root)
        workflows = [
            _workflow_payload(project_root, status)
            for status in statuses
        ]
    except ValueError as exc:
        return validation_error(str(exc))
    return ok(
        {"workflows": workflows},
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


def latest_predictions_response(project_root: Path) -> ApiResponse:
    if (project_root / SCENARIO_PATH).is_file():
        response = latest_rul_predictions_response(project_root)
        if response.status_code == 404:
            return ok({"predictions": []}, "latest predictions retrieved")
        return response
    try:
        predictions = CsvPredictionRepository(
            project_root / "data" / "predictions"
        ).get_latest()
    except ValueError as exc:
        return validation_error(str(exc))

    return ok({"predictions": predictions}, "latest predictions retrieved")


def latest_rul_predictions_response(project_root: Path) -> ApiResponse:
    try:
        repository = CsvPredictionRepository(
            project_root / "data" / "predictions"
        )
        scenario_is_configured = (project_root / SCENARIO_PATH).is_file()
        if scenario_is_configured:
            current_run_ids = current_rul_demo_run_ids(project_root)
            current_predictions = [
                prediction
                for run_id in current_run_ids
                for prediction in repository.get_by_run(run_id)
                if prediction["prediction_type"] == "rul"
            ]
            latest_by_asset: dict[str, dict[str, str]] = {}
            for prediction in current_predictions:
                current = latest_by_asset.get(prediction["asset_id"])
                if (
                    current is None
                    or prediction["scored_at"] > current["scored_at"]
                ):
                    latest_by_asset[prediction["asset_id"]] = prediction
            latest_predictions = list(latest_by_asset.values())
        else:
            latest_predictions = repository.get_latest_by_type("rul")
        if not latest_predictions:
            return not_found("compatible RUL predictions are unavailable")
        demo_asset_ids = (
            configured_rul_demo_asset_ids(project_root)
            if scenario_is_configured
            else {prediction["asset_id"] for prediction in latest_predictions}
        )
        predictions = [
            prediction
            for prediction in latest_predictions
            if prediction["asset_id"] in demo_asset_ids
        ]
    except ValueError as exc:
        return validation_error(str(exc))

    if not predictions:
        return not_found("compatible RUL predictions are unavailable")
    return ok({"predictions": predictions}, "latest RUL predictions retrieved")


def rul_prediction_by_asset_response(
    project_root: Path,
    asset_id: str,
) -> ApiResponse:
    try:
        predictions = [
            prediction
            for prediction in CsvPredictionRepository(
                project_root / "data" / "predictions"
            ).get_by_asset(asset_id)
            if prediction.get("prediction_type") == "rul"
        ]
    except ValueError as exc:
        return validation_error(str(exc))

    if not predictions:
        return not_found(f"RUL prediction unavailable for asset: {asset_id}")
    return ok(
        {"predictions": predictions},
        "RUL prediction history retrieved",
    )
