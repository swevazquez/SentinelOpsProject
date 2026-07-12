# Agent Service

Single operational AI assistant with controlled tool/function calling for asset health questions, prediction explanations, workflow status checks, and approved workflow triggers.

## Operational Query Coordinator

`SCRUM-12` uses the OpenAI Responses API to interpret operational questions and
select from the approved SentinelOps tools. The model can answer questions about:

- list monitored assets,
- rank the highest-risk assets,
- explain the latest prediction for a specified asset,
- summarize workflow execution status,
- and summarize workflow failures.

The assistant returns a grounded answer, structured result items, model metadata,
and tool-use evidence. Tool execution is limited to three sequential rounds, and
tool results are sanitized before they are sent to OpenAI or returned to the
browser. Unsupported questions do not receive access to tools outside the closed
registry.

Automated tests inject a fake Responses client and do not require network access
or an API key. Live model validation is an explicit local or manually triggered
smoke test rather than part of the default CI workflow.

Set `OPENAI_API_KEY` in the server process environment. `OPENAI_MODEL` optionally
overrides the default `gpt-5.4-mini` model. The API key is never returned to the
dashboard.

## Approved Read-Only Tools

`SCRUM-13` defines an explicit registry for asset, workflow, and prediction
lookups. Each tool has a closed input schema and delegates to the existing API
operation boundary. Unknown tools and unexpected arguments are rejected before
execution.

The registry intentionally contains no workflow-trigger or other write-capable
tool. Operational actions remain unavailable until `SCRUM-14` adds an explicit
approval gate.
