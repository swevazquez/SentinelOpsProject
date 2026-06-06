# SentinelOps UI Wireframes

These wireframes define the initial information architecture for the SentinelOps
operational dashboard. They are design artifacts for `SCRUM-27` and a prerequisite
for the `SCRUM-10` implementation of `FR-10`.

The wireframes intentionally describe user needs, screen hierarchy, system states,
and expected data contracts without selecting a frontend framework or implying that
the production dashboard has been implemented.

## Intended Users

| User | Primary Need | Relevant Views |
|---|---|---|
| Maintenance manager | Identify assets requiring attention and understand maintenance priority. | Operations overview, asset details |
| Reliability engineer | Review telemetry trends, prediction factors, and source evidence. | Asset details |
| Operations analyst | Monitor workflow execution and investigate incomplete or failed runs. | Operations overview, workflow details |
| System administrator | Review workflow errors, logs, artifacts, and recovery actions. | Workflow details |
| End user / operator | Obtain understandable operational summaries and guided assistance. | Operations overview, operations assistant |

## Design Rationale

The overview prioritizes exceptions and operational decisions over raw data volume.
Risk, alerts, workflow health, and scoring recency appear first because they answer
the user's initial questions: what needs attention, why, and whether the supporting
workflow is healthy.

Detailed telemetry, prediction evidence, and workflow diagnostics are moved into
focused views. This keeps the overview scannable while preserving traceability from
an operational summary to the asset, workflow run, and generated artifacts that
support it.

The assistant is treated as another controlled client of approved APIs. It displays
tool evidence and separates informational responses from operational actions that
require explicit approval.

## View Specifications

### Operations Overview

**User purpose:** Provide a rapid operational assessment and direct users to assets
or workflow runs that require investigation.

| Panel | User Question | Expected API / Data Source |
|---|---|---|
| Assets at Risk | How many assets currently require attention? | Asset and prediction summary API; latest persisted prediction results |
| Active Alerts | Which conditions are critical or warnings? | Alert or derived maintenance-priority API |
| Workflow Health | Are processing and scoring workflows operating normally? | Workflow status API backed by Airflow run metadata |
| Last Scoring Run | Are displayed predictions recent? | Workflow status and model-run metadata |
| Asset Health | Which individual assets should be reviewed first? | Asset list API joined with latest prediction and maintenance priority |
| Workflow Status | Which runs are active, completed, or failed? | Workflow run list/status API |
| Prediction Summary | How is risk distributed across the monitored assets? | Aggregated prediction result API |

### Asset Details

**User purpose:** Explain an individual asset's condition, prediction, and recommended
maintenance response.

| Panel | User Question | Expected API / Data Source |
|---|---|---|
| Asset Summary | What is the asset's current operational condition? | Asset API and latest telemetry summary |
| Risk Score | How severe is the predicted maintenance risk? | Latest prediction result for the asset |
| Telemetry Trends | Which measurements contributed to the condition? | Time-series telemetry API sourced from persisted telemetry |
| Maintenance Insight | Why was this priority assigned and what action is recommended? | Prediction explanation and recommendation API |
| History | How have risk, workflows, and maintenance events changed? | Prediction history, workflow metadata, and maintenance-event data |

### Workflow Details

**User purpose:** Show ordered execution, identify failures, and provide evidence for
operational recovery.

| Panel | User Question | Expected API / Data Source |
|---|---|---|
| Run Summary | What happened, when, and for how long? | Workflow run status API backed by Airflow metadata |
| Task Execution | Which tasks completed, failed, or were skipped? | Airflow task-instance status and duration data |
| Failure Details | Why did the workflow fail? | Task error summary and approved log retrieval endpoint |
| Recovery Controls | Can the failed task or workflow be run again? | Approval-gated workflow action API |
| Run Artifacts | Which raw and processed outputs belong to this run? | Artifact metadata indexed by shared workflow run ID |

### Operations Assistant

**User purpose:** Provide natural-language access to operational information while
keeping data retrieval auditable and workflow actions approval-gated.

| Panel | User Question | Expected API / Data Source |
|---|---|---|
| Conversation | What operational question was asked and answered? | Agent service conversation state |
| Tool Evidence | Which approved source produced the answer? | Agent tool audit record and API response metadata |
| Suggested Questions | Which supported informational requests are available? | Static supported-query catalog |
| Action Approval | What action is proposed and what will it affect? | Agent action proposal plus workflow action API contract |
| Action State | Was the approved action completed or rejected? | Agent tool result and workflow status API |

## Alternate States

Each implemented view must provide an understandable state rather than an empty or
partially rendered layout.

| State | Expected Behavior |
|---|---|
| Loading | Preserve the page structure and indicate which data is being retrieved. |
| Empty | Explain that no matching assets, predictions, conversations, or workflow runs exist. |
| Failed | Identify the failed operation and provide available diagnostic or recovery actions. |
| Unavailable | Explain which dependency is unavailable without presenting stale data as current. |
| Permission required | Explain that an operational action or protected log requires approval or authorization. |

## Artifacts

| View | Editable Excalidraw | Mermaid Outline | PNG Export |
|---|---|---|---|
| Operations overview | [dashboard-wireframe.excalidraw](dashboard-wireframe.excalidraw) | [dashboard-wireframe.mmd](dashboard-wireframe.mmd) | [dashboard-wireframe.png](../../images/ui/wireframes/dashboard-wireframe.png) |
| Asset details | [asset-details-wireframe.excalidraw](asset-details-wireframe.excalidraw) | [asset-details-wireframe.mmd](asset-details-wireframe.mmd) | [asset-details-wireframe.png](../../images/ui/wireframes/asset-details-wireframe.png) |
| Workflow details | [workflow-details-wireframe.excalidraw](workflow-details-wireframe.excalidraw) | [workflow-details-wireframe.mmd](workflow-details-wireframe.mmd) | [workflow-details-wireframe.png](../../images/ui/wireframes/workflow-details-wireframe.png) |
| Operations assistant | [agent-chat-wireframe.excalidraw](agent-chat-wireframe.excalidraw) | [agent-chat-wireframe.mmd](agent-chat-wireframe.mmd) | [agent-chat-wireframe.png](../../images/ui/wireframes/agent-chat-wireframe.png) |

## Requirement Traceability

| Source | Relationship |
|---|---|
| `SCRUM-27` / `UX-01` | Produces the reviewed wireframes, state definitions, design rationale, and data-dependency annotations. |
| `SCRUM-10` | Uses these artifacts as the design input for the Sprint 2 operational dashboard implementation. |
| `FR-10` | Requires asset health, prediction summaries, and workflow status to be displayed through a dashboard. |
| `FR-05` | Provides the workflow execution states represented by overview and workflow-detail views. |
| `NFR-01` | Requires failed workflow execution to be detectable and reportable. |
| `NFR-05` | Requires clear normal, error, and unavailable API states for future UI integration. |

The Jira relationship records `SCRUM-27` as blocking `SCRUM-10`, ensuring the
dashboard implementation begins from reviewed design artifacts rather than an
untracked interface concept.
