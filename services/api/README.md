# API Service

FastAPI backend for operational endpoints, dashboard data, workflow status, prediction retrieval, and agent coordination.

## Planned Workflow Visibility Contract

`SCRUM-5` adds read-side workflow status helpers that the API service can wrap in
Sprint 2. The API should expose the same status concepts rather than reading raw
JSON files directly:

- lookup one workflow run by run ID,
- list recent workflow runs in newest-first order,
- show `running`, `completed`, and `failed` states,
- include failed step and error details when available,
- and expose aggregate counts for dashboard summaries.
