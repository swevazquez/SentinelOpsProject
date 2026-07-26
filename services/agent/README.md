# Agent Service

Single operational AI assistant with controlled tool/function calling for asset health questions, prediction explanations, workflow status checks, and approved workflow triggers.

## Operational Query Coordinator

`SCRUM-12` uses the OpenAI Responses API to interpret operational questions and
select from the approved SentinelOps tools. The model can answer questions about:

- list monitored assets,
- rank the highest-risk assets,
- compare assets by shortest stored RUL,
- explain the latest prediction for a specified asset,
- explain the stored RUL result for a specified asset,
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

The RUL lookup tools return only compatible stored RUL predictions. If no result
exists, the assistant reports that RUL is unavailable and does not substitute a
rule-based risk score or generated estimate.

The read-only registry intentionally contains no workflow-trigger or other
write-capable tool. Operational actions use the separate approval gate described
below.

## Restricted Operational Actions

`SCRUM-22` defines a separate allowlist for AI-assisted operational actions. The
only supported action is a request to start the `predictive-maintenance`
workflow. Its payload uses a closed schema, rejects unsupported workflows and
extra arguments, and produces a stable SHA-256 fingerprint over the validated
request.

Preparing an action request does not execute the workflow. The request is
immutable and marked as requiring approval so the later approval gate can match
the exact reviewed action before permitting a write. Unknown operations and
direct storage or shell actions are rejected before any side effect.

## Agent Operation Audit Log

`SCRUM-23` records every agent-tool attempt as one JSON Lines event under
`data/audit/agent-operations.jsonl`. Events include a UTC timestamp, a
system-generated correlation ID, the tool name, outcome, duration, and a fixed
error category when applicable. Successful, missing-result, validation-failure,
and unapproved-tool attempts remain distinguishable.

Audit events do not contain tool arguments, model prompts, exception messages,
API keys, or other secrets. Invalid operation names are replaced with a fixed
label instead of being written verbatim. The audit writer also supports action
events so approval decisions can use the same evidence format.

## Approval-Gated Workflow Execution

`SCRUM-14` allows the assistant to prepare the approved workflow action but not
execute it. The service stores an immutable, ten-minute approval record and
returns its impact, expiration, and request fingerprint to the dashboard for
review. An administrator may approve or reject that exact request.

Execution succeeds only when the approval is current, approved, unconsumed, and
matches the prepared action fingerprint. Denied, expired, modified, and replayed
requests are rejected before workflow status or prediction data changes. A
successful execution consumes the approval once and preserves its identifier on
the workflow status record for traceability. The approved action runs the same
default RUL lifecycle checkpoint used by the dashboard and returns a workflow
link in the conversation. The user remains in the Assistant view when the
workflow result is opened and closed.
