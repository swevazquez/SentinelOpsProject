# API Service

FastAPI backend for operational endpoints, dashboard data, workflow status, prediction retrieval, and agent coordination.

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

## Planned Workflow Visibility Contract

`SCRUM-5` adds read-side workflow status helpers that the API service can wrap in
Sprint 2. The API should expose the same status concepts rather than reading raw
JSON files directly:

- lookup one workflow run by run ID,
- list recent workflow runs in newest-first order,
- show `running`, `completed`, and `failed` states,
- include failed step and error details when available,
- and expose aggregate counts for dashboard summaries.
