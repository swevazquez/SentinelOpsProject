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
| `POST` | `/api/assistant/query` | Submit a supported operational query or prepare an approved action. |
| `POST` | `/api/assistant/approvals/{approval_id}` | Approve or reject one prepared action. |
| `POST` | `/api/assistant/actions/execute` | Execute the exact approved action once. |
| `GET` | `/api/predictions/latest` | Retrieve the latest prediction for each asset. |
| `GET` | `/api/predictions/runs/{run_id}` | Retrieve predictions for one workflow run. |
| `GET` | `/api/predictions/assets/{asset_id}` | Retrieve prediction history for one asset. |

Manual requests run in a FastAPI background task and return `202 Accepted` with
a generated run ID. Unsupported workflow names and unexpected request fields
are rejected before execution.

The existing request remains the default rule-based demonstration:

```json
{"workflow": "predictive-maintenance"}
```

After the FD001 data and versioned model are generated, request RUL inference
explicitly:

```json
{
  "workflow": "predictive-maintenance",
  "inference_mode": "rul",
  "model_version": "1.0.0"
}
```

The RUL mode only reads the repository-managed validation trajectory and model
directory. It does not accept arbitrary paths. A missing, corrupt, or
incompatible model or feature contract records a failed workflow step before
prediction persistence. Existing prediction files are not changed.

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
