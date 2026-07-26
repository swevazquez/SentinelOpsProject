from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Literal
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from openai import OpenAIError
from pydantic import BaseModel, ConfigDict

from services.agent.assistant import AssistantModelClient, answer_operational_query
from services.agent.actions import prepare_action_request
from services.agent.approvals import ApprovalError, ApprovalStore
from services.agent.audit import default_audit_logger
from services.api.operations import (
    latest_predictions_response,
    latest_rul_predictions_response,
    list_assets_response,
    predictions_by_asset_response,
    predictions_by_run_response,
    rul_prediction_by_asset_response,
    workflow_list_response,
    workflow_status_response,
)
from services.api.rul_demo import (
    RulDemoBusyError,
    RulDemoCompleteError,
    release_rul_demo_run,
    reserve_rul_demo_batch,
    reset_rul_demo,
    rul_demo_status,
)
from services.api.workflow_execution import run_predictive_workflow
from services.ml.rul_training import DEFAULT_MODEL_VERSION, SEMANTIC_VERSION_PATTERN
from services.workflows.status import record_workflow_status


SUPPORTED_WORKFLOW = "predictive-maintenance"


class WorkflowRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow: str
    inference_mode: Literal["baseline", "rul"] = "rul"
    model_version: str | None = None


class AssistantQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str


class ApprovalDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["approved", "denied"]


class ActionExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_id: str
    action: str
    arguments: dict[str, Any]


def _run_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"manual-{timestamp}-{uuid4().hex[:8]}"


def create_app(
    project_root: Path | None = None,
    assistant_client: AssistantModelClient | None = None,
    approval_store: ApprovalStore | None = None,
) -> FastAPI:
    root = (project_root or Path.cwd()).resolve()
    app = FastAPI(title="SentinelOps API", version="0.1.0")
    approvals = approval_store or ApprovalStore(root)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    def operation_response(response: object) -> JSONResponse:
        return JSONResponse(
            status_code=response.status_code,
            content=response.body,
        )

    @app.get("/api/assets")
    def list_assets() -> JSONResponse:
        return operation_response(list_assets_response(root))

    @app.get("/api/predictions/latest")
    def latest_predictions() -> JSONResponse:
        return operation_response(latest_predictions_response(root))

    @app.get("/api/predictions/rul/latest")
    def latest_rul_predictions() -> JSONResponse:
        return operation_response(latest_rul_predictions_response(root))

    @app.get("/api/predictions/rul/assets/{asset_id}")
    def rul_prediction_by_asset(asset_id: str) -> JSONResponse:
        return operation_response(rul_prediction_by_asset_response(root, asset_id))

    @app.get("/api/predictions/runs/{run_id}")
    def predictions_by_run(run_id: str) -> JSONResponse:
        return operation_response(predictions_by_run_response(root, run_id))

    @app.get("/api/predictions/assets/{asset_id}")
    def predictions_by_asset(asset_id: str) -> JSONResponse:
        return operation_response(predictions_by_asset_response(root, asset_id))

    @app.get("/api/workflows")
    def list_workflows() -> JSONResponse:
        return operation_response(workflow_list_response(root))

    @app.get("/api/workflows/{run_id}")
    def get_workflow(run_id: str) -> dict[str, object]:
        response = workflow_status_response(root, run_id)
        if response.status_code != 200:
            raise HTTPException(response.status_code, response.body["message"])
        return response.body

    @app.get("/api/workflows/rul-demo/status")
    def get_rul_demo_status() -> dict[str, object]:
        try:
            scenario = rul_demo_status(root)
        except ValueError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {
            "status": "ok",
            "request_state": scenario["status"],
            "message": "RUL demo status retrieved",
            "data": {"scenario": scenario},
        }

    @app.post("/api/workflows/rul-demo/reset")
    def reset_rul_demo_scenario() -> dict[str, object]:
        try:
            scenario = reset_rul_demo(root)
        except RulDemoBusyError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {
            "status": "ok",
            "request_state": scenario["status"],
            "message": "RUL demo reset; prior run history was retained",
            "data": {"scenario": scenario},
        }

    @app.post("/api/assistant/query")
    def query_assistant(request: AssistantQueryRequest) -> dict[str, object]:
        if not request.message:
            raise HTTPException(status_code=400, detail="message must not be empty")
        if len(request.message) > 500:
            raise HTTPException(status_code=400, detail="message must not exceed 500 characters")
        try:
            response = answer_operational_query(
                root,
                request.message,
                client=assistant_client,
                approval_store=approvals,
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except (OpenAIError, RuntimeError) as exc:
            raise HTTPException(
                status_code=503,
                detail="the operational assistant is temporarily unavailable",
            ) from exc
        return {
            "status": "ok",
            "request_state": "completed",
            "message": "operational query completed",
            "data": {"response": response},
        }

    @app.post("/api/assistant/approvals/{approval_id}")
    def decide_assistant_action(
        approval_id: str,
        request: ApprovalDecisionRequest,
    ) -> dict[str, object]:
        try:
            approval = approvals.decide(approval_id, request.decision)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ApprovalError as exc:
            raise HTTPException(status_code=_approval_status(exc), detail=str(exc)) from exc
        if request.decision == "denied":
            default_audit_logger(root).record(
                correlation_id=approval.approval_id,
                operation_type="action",
                operation_name=approval.action_name,
                outcome="denied",
                duration_ms=0,
                error_category="approval_denied",
            )
        return {
            "status": "ok",
            "request_state": approval.status,
            "message": f"action {approval.status}",
            "data": {"approval": approval.public_dict()},
        }

    @app.post(
        "/api/assistant/actions/execute",
        status_code=status.HTTP_202_ACCEPTED,
    )
    def execute_assistant_action(
        request: ActionExecutionRequest,
        background_tasks: BackgroundTasks,
    ) -> dict[str, object]:
        started_at = perf_counter()
        action_name = request.action
        try:
            prepared_action = prepare_action_request(
                action_name=action_name,
                arguments=request.arguments,
            )
            scenario = rul_demo_status(root)
            if scenario["status"] == "running":
                raise RulDemoBusyError(
                    f"RUL demo workflow is already running: "
                    f"{scenario['active_run_id']}"
                )
            if scenario["status"] == "complete":
                raise RulDemoCompleteError(
                    "RUL demo scenario is complete; reset it before starting "
                    "another run"
                )
            approval = approvals.authorize(request.approval_id, prepared_action)
        except (RulDemoBusyError, RulDemoCompleteError) as exc:
            _record_action_failure(root, request, started_at, "demo_state_error")
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except LookupError as exc:
            _record_action_failure(root, request, started_at, "approval_not_found")
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            _record_action_failure(root, request, started_at, "validation_error")
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ApprovalError as exc:
            _record_action_failure(root, request, started_at, f"approval_{exc.reason}")
            raise HTTPException(status_code=_approval_status(exc), detail=str(exc)) from exc

        try:
            run_id = _run_id()
            batch = reserve_rul_demo_batch(root, run_id)
            record_workflow_status(
                project_root=root,
                run_id=run_id,
                status="running",
                step="queued",
                approval_id=approval.approval_id,
            )
            approvals.record_execution(approval.approval_id, run_id)
            background_tasks.add_task(
                run_predictive_workflow,
                project_root=root,
                run_id=run_id,
                inference_mode="rul",
                model_version=DEFAULT_MODEL_VERSION,
                rul_trajectory_path=batch.trajectory_path,
            )
        except (RulDemoBusyError, RulDemoCompleteError) as exc:
            _record_action_failure(root, request, started_at, "demo_state_error")
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except Exception:
            if "run_id" in locals():
                release_rul_demo_run(root, run_id)
            _record_action_failure(root, request, started_at, "execution_error")
            raise
        default_audit_logger(root).record(
            correlation_id=approval.approval_id,
            operation_type="action",
            operation_name=prepared_action.name,
            outcome="succeeded",
            duration_ms=(perf_counter() - started_at) * 1000,
        )
        return {
            "status": "accepted",
            "request_state": "accepted",
            "message": "approved predictive maintenance workflow accepted",
            "data": {
                "workflow": {
                    "run_id": run_id,
                    "status": "running",
                    "step": "queued",
                    "approval_id": approval.approval_id,
                    "inference_mode": "rul",
                    "model_version": DEFAULT_MODEL_VERSION,
                    "demo_checkpoint": {
                        "number": batch.checkpoint_index + 1,
                        "label": batch.checkpoint_label,
                    },
                }
            },
        }

    @app.post("/api/workflows", status_code=status.HTTP_202_ACCEPTED)
    def start_workflow(
        request: WorkflowRequest,
        background_tasks: BackgroundTasks,
    ) -> dict[str, object]:
        if request.workflow != SUPPORTED_WORKFLOW:
            raise HTTPException(
                status_code=400,
                detail=f"unsupported workflow: {request.workflow}",
            )
        if request.inference_mode == "baseline" and request.model_version is not None:
            raise HTTPException(
                status_code=400,
                detail="model_version is only supported for RUL inference",
            )
        model_version = request.model_version or DEFAULT_MODEL_VERSION
        if not SEMANTIC_VERSION_PATTERN.fullmatch(model_version):
            raise HTTPException(
                status_code=400,
                detail="model_version must use semantic MAJOR.MINOR.PATCH format",
            )
        run_id = _run_id()
        batch = None
        if request.inference_mode == "rul":
            try:
                batch = reserve_rul_demo_batch(root, run_id)
            except (RulDemoBusyError, RulDemoCompleteError) as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            except ValueError as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
        record_workflow_status(
            project_root=root,
            run_id=run_id,
            status="running",
            step="queued",
        )
        background_tasks.add_task(
            run_predictive_workflow,
            project_root=root,
            run_id=run_id,
            inference_mode=request.inference_mode,
            model_version=model_version,
            rul_trajectory_path=batch.trajectory_path if batch else None,
        )
        return {
            "status": "accepted",
            "request_state": "accepted",
            "message": "predictive maintenance workflow accepted",
            "data": {
                "workflow": {
                    "run_id": run_id,
                    "status": "running",
                    "step": "queued",
                    "inference_mode": request.inference_mode,
                    "model_version": (
                        model_version if request.inference_mode == "rul" else None
                    ),
                    "demo_checkpoint": (
                        {
                            "number": batch.checkpoint_index + 1,
                            "label": batch.checkpoint_label,
                        }
                        if batch
                        else None
                    ),
                }
            },
        }

    dashboard_dir = root / "frontend" / "dashboard"
    if dashboard_dir.exists():
        app.mount("/", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")

    return app


def _approval_status(error: ApprovalError) -> int:
    if error.reason == "expired":
        return status.HTTP_410_GONE
    if error.reason in ("mismatch", "replayed", "already_decided", "invalid_status"):
        return status.HTTP_409_CONFLICT
    return status.HTTP_403_FORBIDDEN


def _record_action_failure(
    project_root: Path,
    request: ActionExecutionRequest,
    started_at: float,
    error_category: str,
) -> None:
    default_audit_logger(project_root).record(
        correlation_id=request.approval_id,
        operation_type="action",
        operation_name=request.action,
        outcome="rejected",
        duration_ms=(perf_counter() - started_at) * 1000,
        error_category=error_category,
    )


app = create_app()
