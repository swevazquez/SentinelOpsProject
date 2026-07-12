from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from openai import OpenAIError
from pydantic import BaseModel, ConfigDict

from services.agent.assistant import AssistantModelClient, answer_operational_query
from services.api.operations import (
    latest_predictions_response,
    list_assets_response,
    workflow_list_response,
    workflow_status_response,
)
from services.api.workflow_execution import run_predictive_workflow
from services.workflows.status import record_workflow_status


SUPPORTED_WORKFLOW = "predictive-maintenance"


class WorkflowRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow: str


class AssistantQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str


def _run_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"manual-{timestamp}-{uuid4().hex[:8]}"


def create_app(
    project_root: Path | None = None,
    assistant_client: AssistantModelClient | None = None,
) -> FastAPI:
    root = (project_root or Path.cwd()).resolve()
    app = FastAPI(title="SentinelOps API", version="0.1.0")
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

    @app.get("/api/workflows")
    def list_workflows() -> JSONResponse:
        return operation_response(workflow_list_response(root))

    @app.get("/api/workflows/{run_id}")
    def get_workflow(run_id: str) -> dict[str, object]:
        response = workflow_status_response(root, run_id)
        if response.status_code != 200:
            raise HTTPException(response.status_code, response.body["message"])
        return response.body

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
        run_id = _run_id()
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
                }
            },
        }

    dashboard_dir = root / "frontend" / "dashboard"
    if dashboard_dir.exists():
        app.mount("/", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")

    return app


app = create_app()
