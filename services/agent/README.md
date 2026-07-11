# Agent Service

Single operational AI assistant with controlled tool/function calling for asset health questions, prediction explanations, workflow status checks, and approved workflow triggers.

## Approved Read-Only Tools

`SCRUM-13` defines an explicit registry for asset, workflow, and prediction
lookups. Each tool has a closed input schema and delegates to the existing API
operation boundary. Unknown tools and unexpected arguments are rejected before
execution.

The registry intentionally contains no workflow-trigger or other write-capable
tool. Operational actions remain unavailable until `SCRUM-14` adds an explicit
approval gate.
