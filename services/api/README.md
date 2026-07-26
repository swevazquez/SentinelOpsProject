# API Service

FastAPI backend for operational endpoints, dashboard data, workflow status, prediction retrieval, and agent coordination.

## Local API and Dashboard

Install the project dependencies and start the FastAPI application from the
repository root:

```bash
uv sync --extra dev
uv run uvicorn services.api.app:app --reload
```

Open `http://127.0.0.1:8000`. The application serves the dashboard and the
workflow API from the same origin.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/assets` | Retrieve configured asset profiles for the dashboard. |
| `POST` | `/api/workflows` | Start the approved `predictive-maintenance` workflow. |
| `GET` | `/api/workflows` | List workflow execution states. |
| `GET` | `/api/workflows/{run_id}` | Retrieve one workflow execution state. |
| `GET` | `/api/workflows/rul-demo/status` | Retrieve the repeatable RUL scenario checkpoint and engine set. |
| `POST` | `/api/workflows/rul-demo/reset` | Start a new scenario session without deleting prior run evidence. |
| `POST` | `/api/assistant/query` | Submit a supported operational query or prepare an approved action. |
| `POST` | `/api/assistant/approvals/{approval_id}` | Approve or reject one prepared action. |
| `POST` | `/api/assistant/actions/execute` | Execute the exact approved action once. |
| `GET` | `/api/predictions/latest` | Retrieve the latest prediction for each asset. |
| `GET` | `/api/predictions/rul/latest` | Retrieve only the latest compatible RUL predictions. |
| `GET` | `/api/predictions/rul/assets/{asset_id}` | Retrieve only stored RUL history for one asset. |
| `GET` | `/api/predictions/runs/{run_id}` | Retrieve predictions for one workflow run. |
| `GET` | `/api/predictions/assets/{asset_id}` | Retrieve prediction history for one asset. |

Manual requests run in a FastAPI background task and return `202 Accepted` with
a generated run ID. Unsupported workflow names and unexpected request fields
are rejected before execution.

The minimal request runs the default RUL demonstration:

```json
{"workflow": "predictive-maintenance"}
```

It uses four held-out FD001 engines and advances them through 40%, 60%, 80%, and
100% lifecycle checkpoints. Each accepted run persists a unique label-free
trajectory and metadata record before applying the trained model. A fifth run is
blocked until the scenario is reset, and reset retains all prior inputs,
workflow records, and predictions while clearing them from the new session's
active RUL view. Completed workflow responses include a result summary with
condition counts, finding severity, highest risk, and shortest RUL.

The model version may be selected explicitly:

```json
{
  "workflow": "predictive-maintenance",
  "inference_mode": "rul",
  "model_version": "1.0.0"
}
```

The RUL mode only reads the repository-managed scenario, validation trajectory,
and model directory. It does not accept arbitrary paths. A missing, corrupt, or
incompatible prerequisite produces an unavailable or failed response before a
new prediction file replaces any existing result. For local development and
deterministic tests, send `"inference_mode": "baseline"` explicitly.

## Operational API Contract

`SCRUM-9` adds API-facing operation handlers for the current Sprint 2 data
contracts. These handlers provide the behavior that FastAPI routes should expose:

| Operation | Data Source | Response |
|---|---|---|
| Health | API service metadata | Service name and healthy state |
| Assets | `data/samples/asset_profiles.csv` | Configured asset profiles |
| Workflow by run | `data/workflow-status/` | One workflow run or a not-found response |
| Workflow list | `data/workflow-status/` | Recent workflow runs in newest-first order |
| Workflow summary | `data/workflow-status/` | Running, completed, failed, and total counts |
| Predictions by run | `data/predictions/` | Prediction records for one workflow run |
| Predictions by asset | `data/predictions/` | Prediction history for one asset |
| Latest RUL predictions | `data/predictions/` | Latest RUL record for each compatible asset |
| RUL predictions by asset | `data/predictions/` | RUL-only history or an explicit unavailable response |

The response contract uses a status code and a JSON-compatible body. All
responses include `status`, `request_state`, and `message`. Successful responses
also include `data`.

| State | Status Code | Body Shape |
|---|---:|---|
| Normal | 200 | `{"status": "ok", "request_state": "ok", "message": "...", "data": ...}` |
| Missing resource | 404 | `{"status": "not_found", "request_state": "not_found", "message": "..."}` |
| Invalid request or malformed source data | 400 | `{"status": "error", "request_state": "error", "message": "..."}` |
| Unavailable source | 503 | `{"status": "unavailable", "request_state": "unavailable", "message": "..."}` |

## Workflow Visibility Contract

Workflow status and prediction routes expose the same status concepts used by
the stored operational records rather than requiring clients to read raw files:

- lookup one workflow run by run ID,
- list recent workflow runs in newest-first order,
- show `running`, `completed`, and `failed` states,
- include failed step and error details when available,
- and expose aggregate counts for dashboard summaries.
