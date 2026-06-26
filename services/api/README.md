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

The response contract uses a status code and a JSON-compatible body. Successful
responses use `{"status": "ok", "data": ...}`. Missing resources return
`404` with `{"status": "not_found", "message": ...}`. Validation failures return
`400` with `{"status": "error", "message": ...}`.

## Planned Workflow Visibility Contract

`SCRUM-5` adds read-side workflow status helpers that the API service can wrap in
Sprint 2. The API should expose the same status concepts rather than reading raw
JSON files directly:

- lookup one workflow run by run ID,
- list recent workflow runs in newest-first order,
- show `running`, `completed`, and `failed` states,
- include failed step and error details when available,
- and expose aggregate counts for dashboard summaries.
