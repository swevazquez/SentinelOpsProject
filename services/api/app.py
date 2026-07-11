from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

from services.api.operations import workflow_list_response, workflow_status_response
from services.api.workflow_execution import run_predictive_workflow
from services.workflows.status import record_workflow_status


SUPPORTED_WORKFLOW = "predictive-maintenance"


class WorkflowRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow: str


def _run_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"manual-{timestamp}-{uuid4().hex[:8]}"


def create_app(project_root: Path | None = None) -> FastAPI:
    root = (project_root or Path.cwd()).resolve()
    app = FastAPI(title="SentinelOps API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.get("/api/workflows")
    def list_workflows() -> dict[str, object]:
        response = workflow_list_response(root)
        return response.body

    @app.get("/api/workflows/{run_id}")
    def get_workflow(run_id: str) -> dict[str, object]:
        response = workflow_status_response(root, run_id)
        if response.status_code != 200:
            raise HTTPException(response.status_code, response.body["message"])
        return response.body

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
