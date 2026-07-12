# SentinelOps Weekly Progress Report

# 1. Report Metadata

| Field | Value |
|---|---|
| Course | SWENG 894 - Software Engineering Capstone Experience |
| Project | SentinelOps |
| Student | Eli Vazquez |
| Sprint | Sprint 3 |
| Reporting Week | Week 7 |
| Reporting Period | 2026-07-06 to 2026-07-12 |
| Report Date | 2026-07-12 |
| Report Status | Current through 2026-07-12 |
| Git Repository | <https://github.com/swevazquez/SentinelOpsProject> |
| Jira Board | <https://psu-capstone-sentinelops.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog> |

---

# 2. Sprint Goal and Planning

Sprint 3 extends the predictive-maintenance MVP with controlled user interaction. The sprint goal is to support manual workflow execution, expose approved read-only agent tools, and establish the foundation for AI-assisted operational queries and approval-gated actions. The significant algorithmic component proposal was also completed so instructor feedback can guide the later machine-learning implementation.

## Groomed Product Backlog and Highest-Priority Sprint Backlog

| Jira / Requirement | Backlog Item | Priority | Estimate | Current Status |
|---|---|---:|---:|---|
| SCRUM-11 / FR-11 | Manual Workflow Execution | Medium | 3 SP | Done |
| SCRUM-12 / FR-12 | AI-Assisted Operational Queries | Low | 5 SP | To Do |
| SCRUM-13 / FR-13 | Controlled Agent Tool Access | Low | 3 SP | Done |
| SCRUM-14 / FR-14 | Approval-Gated Operational Actions | Low | 3 SP | To Do |
| SCRUM-22 / NFR-06 | Restricted AI-Assisted Workflow Actions | High | 3 SP | To Do |
| SCRUM-23 / NFR-07 | Agent Tool Usage Logging | Medium | 2 SP | To Do |
| SCRUM-28 / SAC | ML-Based Remaining Useful Life Algorithm Specification | High | 3 SP | Done |

Sprint 3 contains 22 story points. Nine points are complete and 13 remain. The completed work exceeds the one-third progress target for the first reporting week.

## Definition of Done

| Area | Criteria Applied to Every Sprint Item |
|---|---|
| Requirements | Scope and Given/When/Then acceptance criteria are documented in Jira and traceable to the source requirement. |
| Design | Affected API, workflow, data, security, agent-tool, or UI behavior is documented before implementation. |
| Development | The behavior is implemented within the existing component boundaries with no uncontrolled writes or speculative infrastructure. |
| Testing | Focused success, validation, and failure-path tests are added or specified. |
| Integration | The feature is exercised through its actual boundary, including UI-to-API behavior when applicable. |
| Documentation | Reviewer-facing setup, interfaces, evidence, and architectural rationale are updated. |
| Review | Changes are committed with the Jira key and submitted through a story-specific pull request. |
| Validation | Focused tests and the full CI validation pass; user-facing changes receive responsive inspection. |

## Acceptance Criteria

| Requirement | Acceptance Criteria |
|---|---|
| FR-11 | Given the supported predictive-maintenance workflow, when a user starts it from the dashboard, then the API returns a run ID and the UI displays running, completed, or failed status. Unsupported or malformed requests do not execute. |
| FR-12 | Given the assistant is available, when a user submits a supported asset, prediction, or workflow question, then the response is derived from an approved operational tool and identifies unavailable information clearly. |
| FR-13 | Given an assistant tool request, when the tool is resolved, then only a registered read-only tool with validated arguments can execute through the API operation boundary. |
| FR-14 | Given an assistant requests an operational action, when approval has not been granted, then no workflow starts; after explicit approval, only the reviewed request may execute once. |
| NFR-06 | Given an AI-assisted action request, when its operation is not predefined and approved, then it is rejected before an operational write occurs. |
| NFR-07 | Given an agent tool is attempted, when it succeeds or fails, then tool name, time, request context, outcome, and non-sensitive error evidence are recorded for review. |
| SAC | Given the current MVP and NASA C-MAPSS FD001, when the specification is reviewed, then it clearly defines the Random Forest RUL algorithm, flow, value, evaluation, integration, and post-feedback implementation strategy in no more than three PDF pages. |

---

# 3. UI Design

SCRUM-11 extended the existing dashboard wireframe into a live workflow interaction. The Workflows view now starts the supported predictive-maintenance workflow through FastAPI, shows the execution state, refreshes live asset and prediction data, and presents explicit loading, success, error, and empty states. Raw run identifiers remain available as traceability metadata while the visible label is presented as a readable manual execution entry.

| View | Sprint Coverage | Evidence |
|---|---|---|
| Overview | FR-11 workflow health, latest scoring run, prediction distribution | `frontend/dashboard/index.html`, `frontend/dashboard/app.js` |
| Assets | Live asset profiles and latest per-asset predictions | `GET /api/assets`, `GET /api/predictions/latest` |
| Workflows | Manual execution, state counts, execution history, and failure state | `POST /api/workflows`, `GET /api/workflows` |
| Assistant | Reserved for FR-12; current state clearly identifies that assistant integration is not yet enabled | `frontend/dashboard/index.html` |

The Assistant view remains intentionally limited until FR-12 is implemented. This avoids presenting static assistant behavior as if it were connected to the agent service.

---

# 4. Backlog Grooming

| Change | Item | Description and Rationale | Impact |
|---|---|---|---|
| Sprint transition | Sprint 2 / Sprint 3 | Sprint 2 was closed and Sprint 3 was activated for the 2026-07-06 through 2026-07-26 window. | Establishes the current sprint baseline. |
| Added | SCRUM-28 / SAC | Added a 3-point specification story for the required significant algorithmic component. | Makes proposal work visible without starting ML implementation before instructor feedback. |
| Estimated | SCRUM-22 / NFR-06 | Assigned 3 points for action allowlisting and enforcement. | Makes the security work visible in capacity planning. |
| Estimated | SCRUM-23 / NFR-07 | Assigned 2 points for structured agent-tool audit logging. | Completes the 22-point Sprint 3 baseline. |
| Refined | FR-11 | Included FastAPI routing, background execution, live workflow status, dashboard interaction, and CI dependency setup. | Delivers an end-to-end workflow rather than a backend-only helper. |
| Deferred | ML implementation | ML training and inference stories remain deferred until instructor feedback on the SAC is received. | Prevents premature scope while preserving the implementation path. |

No significant backlog changes occurred beyond the grooming updates listed above. The remaining Sprint 3 backlog remains aligned with the sprint goal and MVP delivery strategy.

---

# 5. Source Code Development

## Summary of Contributions

This week delivered the first Sprint 3 vertical slice across the API, dashboard, agent boundary, and documentation:

- Added manual workflow execution with FastAPI validation, background execution, run identifiers, and status persistence.
- Integrated the dashboard with live asset profiles, latest predictions, workflow states, refresh behavior, and responsive empty/error states.
- Added controlled read-only agent tools with closed schemas, exact argument validation, API operation delegation, and structured results.
- Added the significant algorithmic component proposal for a NASA C-MAPSS FD001 Random Forest remaining-useful-life model.
- Corrected CI dependency installation so the integration tests execute in GitHub Actions.

## Repository Information

| Resource | Link |
|---|---|
| Git Repository | <https://github.com/swevazquez/SentinelOpsProject> |
| Jira Board | <https://psu-capstone-sentinelops.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog> |

## Important Commits

| Commit | Commit Summary | Related Requirement / User Story | Notes |
|---|---|---|---|
| [`b49b145`](https://github.com/swevazquez/SentinelOpsProject/commit/b49b1456f3cea66179ccdfd4c881f83cf0129f8b) | Integrate dashboard with live workflow data | SCRUM-11 / FR-11 | Adds live API-backed dashboard data, workflow execution UI, read endpoints, and tests. |
| [`a317c23`](https://github.com/swevazquez/SentinelOpsProject/commit/a317c23701da3a0986a0d8bea55e74f3daf894e5) | Install CI dependencies without packaging the repository | SCRUM-11 / FR-11 | Ensures GitHub Actions installs runtime and test dependencies for the integration suite. |
| [`4024813`](https://github.com/swevazquez/SentinelOpsProject/commit/4024813c631fa6b38fd409021567a7bf24e67ebd) | Merge manual workflow execution pull request | SCRUM-11 / FR-11 | Merges PR [#20](https://github.com/swevazquez/SentinelOpsProject/pull/20) into `main`. |
| [`7c18d61`](https://github.com/swevazquez/SentinelOpsProject/commit/7c18d6165d8c6ab7afc9c1fdcb250edaa42d46b7) | Add controlled agent tools | SCRUM-13 / FR-13 | Adds the approved read-only registry, schemas, API delegation, and unit tests. |
| [`9b3a101`](https://github.com/swevazquez/SentinelOpsProject/commit/9b3a101eeb0f49a50f501ef341dc2a218b0eb39e) | Merge controlled agent tool access pull request | SCRUM-13 / FR-13 | Merges PR [#21](https://github.com/swevazquez/SentinelOpsProject/pull/21) into `main`. |
| [`96aa1b1`](https://github.com/swevazquez/SentinelOpsProject/commit/96aa1b173ed96b74ece4d937b201fb318279d47f) | Refine algorithmic component proposal | SCRUM-28 / SAC | Finalizes the reviewer-facing proposal format and removes export-only styling from the Markdown source. |
| [`267861d`](https://github.com/swevazquez/SentinelOpsProject/commit/267861da957d84f70909a802c7a63cf182fd9451) | Merge significant algorithmic component proposal | SCRUM-28 / SAC | Merges PR [#19](https://github.com/swevazquez/SentinelOpsProject/pull/19) into `main`. |

## Burndown Summary

| Metric | Value |
|---|---:|
| Sprint Total Estimated Effort | 22 story points |
| Completed Effort | 9 story points |
| Remaining Effort | 13 story points |
| Completion Rate | 40.9% |
| Sprint Status | On track; more than one-third completed in the first reporting week |

![Sprint 3 Week 7 Burndown](../images/reports/week-07-burndown.svg)

---

# 6. Software Testing

## Testing Overview

Testing this week covered the completed FR-11, FR-13, and SAC work and established reproducible specifications for the remaining Sprint 3 requirements. SCRUM-11’s focused API/UI suite passed 25 tests locally, SCRUM-13’s focused agent-tool suite passed 4 tests, and the GitHub CI checks for PRs #20 and #21 passed after the dependency-installation correction.

## Requirement-to-Test Traceability Matrix

| Requirement | Test Case | Type | Test Objective | Status / Evidence |
|---|---|---|---|---|
| FR-11 | TC-FR11-01 | Integration / UI | Start the supported workflow, observe status, refresh live data, and reject invalid requests. | Passed; `tests/integration/test_manual_workflow_api.py`, `tests/unit/test_dashboard_ui.py`, PR [#20](https://github.com/swevazquez/SentinelOpsProject/pull/20) |
| FR-12 | TC-FR12-01 | Integration / UAT | Answer supported operational questions through approved tools. | Planned; assistant service not yet implemented. |
| FR-13 | TC-FR13-01 | Unit | Enforce the approved read-only registry, closed schemas, and exact arguments. | Passed; `tests/unit/test_agent_tools.py`, PR [#21](https://github.com/swevazquez/SentinelOpsProject/pull/21) |
| FR-14 | TC-FR14-01 | Integration / Security | Block unapproved actions and execute one explicitly approved action. | Planned. |
| NFR-06 | TC-NFR06-01 | Security | Reject undefined or non-approved AI operations before writes. | Planned. |
| NFR-07 | TC-NFR07-01 | Unit / Audit | Record reviewable tool-attempt evidence without sensitive arguments. | Planned. |
| SAC | TC-SAC-01 | Document Review | Verify rubric coverage, visual clarity, rationale, and page-limit compliance. | Passed; `docs/algorithmic-component.md`, PR [#19](https://github.com/swevazquez/SentinelOpsProject/pull/19) |
| Sprint 3 baseline | TC-SPRINT3-01 | Regression / CI | Run the full test suite, workflow smoke test, DAG syntax check, generated-data safeguards, and Markdown checks. | Passed in PR #20 and PR #21 CI. |

## Test Case Specifications

### TC-FR11-01 - Manual Predictive Workflow Execution

| Field | Description |
|---|---|
| Related Requirement | SCRUM-11 / FR-11 |
| Test Type | Integration / UI |
| Objective | Verify the supported workflow can be started from the API and dashboard, reaches a terminal state, and rejects invalid requests. |
| Preconditions | Repository on the merged Sprint 3 `main`; Python 3.12; project dependencies installed; sample asset profiles present. |
| Test Data / Parameters | `predictive-maintenance`; `unapproved-workflow`; malformed payload with unexpected `hours`. |
| Execution Environment | Local Python environment and FastAPI TestClient; dashboard served by Uvicorn for manual review. |
| Expected Final Result | Valid requests return HTTP 202 with a file-safe run ID; status and prediction artifacts are created; invalid requests return 400 or 422 without starting a workflow. |
| Actual Result | 25 focused API, operation, and dashboard tests passed. GitHub CI for PR #20 passed. |
| Evidence | `tests/integration/test_manual_workflow_api.py`, `tests/unit/test_api_operations.py`, `tests/unit/test_dashboard_ui.py`, PR [#20](https://github.com/swevazquez/SentinelOpsProject/pull/20). |
| Cleanup / Reset | Generated runtime files remain ignored; stop Uvicorn after manual review. |
| Status | Passed |

#### Execution Steps

1. Run `UV_CACHE_DIR=/tmp/sentinelops-uv-cache uv run pytest tests/integration/test_manual_workflow_api.py tests/unit/test_api_operations.py tests/unit/test_dashboard_ui.py`.
   - Expected result: 25 tests pass.
2. Start `uv run uvicorn services.api.app:app --reload` from the repository root and open `http://127.0.0.1:8000`.
   - Expected result: The SentinelOps dashboard opens on Overview and loads API-backed data.
3. Open Workflows and select **Run workflow**.
   - Expected result: The button disables, a status message appears, and a manual execution entry is added.
4. Refresh the workflow view after execution completes.
   - Expected result: The run is shown as completed or failed with a readable label and traceable run metadata.
5. Submit an unsupported workflow name and a payload with an unexpected field through the API tests or `curl`.
   - Expected result: The unsupported request returns 400, the malformed request returns 422, and no invalid workflow starts.
6. Stop Uvicorn and confirm generated runtime files are not staged by Git.
   - Expected result: The repository remains clean except for intentionally changed source files.

### TC-FR12-01 - AI-Assisted Operational Query

| Field | Description |
|---|---|
| Related Requirement | SCRUM-12 / FR-12 |
| Test Type | Integration / User Acceptance |
| Objective | Verify supported asset, prediction, and workflow questions use approved tools and return evidence-backed answers. |
| Preconditions | FR-13 tools and the FR-12 assistant service/UI are implemented; sample operational records exist. |
| Test Data / Parameters | Questions for an existing asset, workflow, prediction, unknown asset, and unsupported request. |
| Execution Environment | Local API, dashboard, configured model provider, and test fixtures. |
| Expected Final Result | Supported questions return data from the matching approved tool; missing or unsupported information is stated clearly without fabricated results. |
| Actual Result | Not yet executed; FR-12 remains To Do in Jira. |
| Evidence | Planned FR-12 integration test, assistant transcript fixture, and UI evidence. |
| Cleanup / Reset | Remove temporary conversation and model-response fixtures. |
| Status | Planned |

#### Planned Execution Steps

1. Start the API and assistant UI with the documented local configuration.
   - Expected result: The Assistant view loads and reports service readiness.
2. Submit a supported asset question.
   - Expected result: The assistant selects `list_assets` or the appropriate approved lookup and cites the returned asset data.
3. Submit workflow and prediction questions.
   - Expected result: The corresponding approved tools execute and the answer includes current operational evidence.
4. Submit an unknown-asset and unsupported question.
   - Expected result: The assistant reports unavailable or unsupported information without calling an unapproved tool.
5. Run the focused FR-12 test and `./scripts/check-ci.sh`.
   - Expected result: Focused and regression tests pass.

### TC-FR13-01 - Controlled Read-Only Tool Registry

| Field | Description |
|---|---|
| Related Requirement | SCRUM-13 / FR-13 |
| Test Type | Unit |
| Objective | Verify only explicitly registered, read-only tools with closed schemas can execute. |
| Preconditions | Repository on merged SCRUM-13; temporary asset, workflow, and prediction fixtures available. |
| Test Data / Parameters | Five approved tools; valid arguments; missing/extra arguments; unknown `run_workflow`. |
| Execution Environment | Python 3.12 local environment and temporary filesystem. |
| Expected Final Result | Approved tools return structured API data; unknown tools and invalid arguments are rejected; all registered tools are read-only. |
| Actual Result | Four focused tests passed. PR #21 GitHub checks passed. |
| Evidence | `services/agent/tools.py`, `tests/unit/test_agent_tools.py`, PR [#21](https://github.com/swevazquez/SentinelOpsProject/pull/21). |
| Cleanup / Reset | Temporary fixtures are removed automatically. |
| Status | Passed |

#### Execution Steps

1. Run `.venv/bin/python -m unittest tests/unit/test_agent_tools.py -v`.
   - Expected result: Four tests pass.
2. Inspect `tool_schemas()` output.
   - Expected result: Every function schema sets `additionalProperties` to false.
3. Execute each approved lookup with valid arguments.
   - Expected result: Structured operational data is returned with `read_only: true`.
4. Execute an unknown tool and missing/extra argument cases.
   - Expected result: Validation errors are raised before any operation executes.
5. Run the full CI command.
   - Expected result: Agent tests and the existing regression suite pass together.

### TC-FR14-01 - Approval-Gated Agent Action

| Field | Description |
|---|---|
| Related Requirement | SCRUM-14 / FR-14 |
| Test Type | Integration / Security |
| Objective | Verify an operational action cannot execute without explicit approval and that an approval authorizes only one reviewed request. |
| Preconditions | FR-11 workflow endpoint, FR-13 registry, and FR-14 approval state are implemented. |
| Test Data / Parameters | Valid action, denied request, expired approval, replayed approval, and modified post-approval payload. |
| Execution Environment | Local API/assistant service with temporary workflow-status storage. |
| Expected Final Result | Denied, expired, replayed, or modified requests create no workflow; one matching approved request starts exactly once. |
| Actual Result | Not yet executed; FR-14 remains To Do in Jira. |
| Evidence | Planned FR-14 integration tests, approval record, workflow-status output, and UI approval screenshot. |
| Cleanup / Reset | Remove temporary approval and workflow-status fixtures. |
| Status | Planned |

#### Planned Execution Steps

1. Submit an operational action without approval.
   - Expected result: The request is rejected and no workflow status file is created.
2. Submit the same request with an expired or denied approval.
   - Expected result: The request remains rejected with no side effect.
3. Approve the exact request and submit it once.
   - Expected result: One workflow starts and records the approval reference.
4. Replay the approval or modify the approved payload.
   - Expected result: The request is rejected and no second workflow starts.
5. Run focused security tests and full CI.
   - Expected result: All approval and regression assertions pass.

### TC-NFR06-01 - Restricted AI-Assisted Operations

| Field | Description |
|---|---|
| Related Requirement | SCRUM-22 / NFR-06 |
| Test Type | Security |
| Objective | Verify AI-assisted operations are restricted to predefined approved operations. |
| Preconditions | FR-13 registry and FR-14 approval gate are implemented. |
| Test Data / Parameters | Approved read, approved gated action, unknown operation, direct storage mutation, malformed arguments. |
| Execution Environment | Local agent service with temporary storage fingerprints. |
| Expected Final Result | Unknown and direct-mutation requests are rejected before side effects; writes require the approval gate. |
| Actual Result | Not yet executed; NFR-06 remains To Do in Jira. |
| Evidence | Planned NFR-06 security test output and before/after storage fingerprints. |
| Cleanup / Reset | Remove temporary security fixtures. |
| Status | Planned |

#### Planned Execution Steps

1. Record the initial workflow and prediction storage fingerprints.
   - Expected result: Baseline state is captured.
2. Submit approved read and unknown operation requests.
   - Expected result: Reads execute through the registry; unknown operations are rejected.
3. Submit a direct storage mutation request.
   - Expected result: The request is rejected and fingerprints remain unchanged.
4. Submit a write-capable action without approval.
   - Expected result: No workflow or storage mutation occurs.
5. Run the security tests and full CI.
   - Expected result: All restrictions pass and no unauthorized side effect is recorded.

### TC-NFR07-01 - Agent Tool Usage Logging

| Field | Description |
|---|---|
| Related Requirement | SCRUM-23 / NFR-07 |
| Test Type | Unit / Audit |
| Objective | Verify every tool attempt produces reviewable, sanitized evidence. |
| Preconditions | Structured agent audit logging is implemented with a temporary log destination. |
| Test Data / Parameters | Successful lookup, validation failure, missing result, rejected tool, approved action, denied action. |
| Execution Environment | Local agent service and temporary audit log. |
| Expected Final Result | Each attempt records timestamp, tool, correlation context, outcome, duration, and sanitized error category without secrets or raw sensitive arguments. |
| Actual Result | Not yet executed; NFR-07 remains To Do in Jira. |
| Evidence | Planned audit-log tests and parsed audit fixture. |
| Cleanup / Reset | Remove temporary audit logs. |
| Status | Planned |

#### Planned Execution Steps

1. Configure the audit logger to a temporary destination.
   - Expected result: The destination is writable and isolated from project data.
2. Execute successful, failed, rejected, and denied tool cases.
   - Expected result: Each attempt produces one structured event.
3. Parse the audit records.
   - Expected result: Required fields are present and outcomes are distinguishable.
4. Inspect for forbidden fields.
   - Expected result: Secrets and raw sensitive arguments are absent or redacted.
5. Run audit tests and full CI.
   - Expected result: Logging behavior passes without changing tool outcomes.

### TC-SAC-01 - Significant Algorithmic Component Specification Review

| Field | Description |
|---|---|
| Related Requirement | SCRUM-28 / SAC |
| Test Type | Document Review |
| Objective | Verify the proposal clearly defines the product context, Random Forest RUL algorithm, flow, rationale, feasibility, and implementation strategy. |
| Preconditions | `docs/algorithmic-component.md` and `docs/images/algorithmic-component-flow.svg` are available. |
| Test Data / Parameters | Proposal Markdown and visual flow diagram. |
| Execution Environment | Markdown review and external PDF export by the student. |
| Expected Final Result | The proposal addresses WHAT, HOW, and WHY, includes a helpful visual aid, and remains within the three-page PDF limit. |
| Actual Result | Proposal merged through PR #19; Markdown source is clean and ready for professor review/export. |
| Evidence | `docs/algorithmic-component.md`, `docs/images/algorithmic-component-flow.svg`, PR [#19](https://github.com/swevazquez/SentinelOpsProject/pull/19). |
| Cleanup / Reset | The Markdown source and diagram remain available for review. |
| Status | Passed |

#### Execution Steps

1. Read the Product Overview section.
   - Expected result: SentinelOps users, problem, and predictive-maintenance role are clear.
2. Read the Algorithmic Solution Specification.
   - Expected result: data preparation, temporal feature engineering, Random Forest training, validation, versioning, inference, and maintenance mapping are explained.
3. Inspect the flow diagram.
   - Expected result: offline training and runtime scoring behavior are understandable.
4. Read the rationale and implementation strategy.
   - Expected result: WHAT, HOW, and WHY include feasibility, value, limitations, and integration sequencing.
5. Export the Markdown externally and verify the page count.
   - Expected result: The PDF is readable and does not exceed three pages.

## Testing Summary

Completed requirements have focused automated coverage and passing CI evidence. Remaining Sprint 3 requirements have complete planned test specifications so implementation can be validated against the same acceptance criteria as the work is added. The main testing risk is preserving the approval, restriction, and audit boundaries while the assistant service is integrated.

---

# 7. Risks, Roadblocks, and Mitigation

| Risk / Roadblock | Impact | Mitigation / Next Step |
|---|---|---|
| Instructor feedback may change the SAC direction. | ML implementation work could require redesign. | Keep implementation stories deferred until feedback and preserve the proposal’s phased strategy. |
| The proposed NASA FD001 schema may differ from current simulator telemetry. | Training and runtime feature transformations may not be directly reusable. | Define a versioned feature contract and validate offline and runtime transformations independently. |
| FR-12, FR-14, NFR-06, and NFR-07 cross the model, UI, API, and security boundaries. | Assistant scope could expand faster than the remaining schedule. | Deliver one read-only query path first, then one narrow approval-gated action with logging. |
| Framework adoption could add unnecessary complexity. | Integration and testing effort could displace required stories. | Keep the existing registry framework-neutral and use native tool calling before evaluating LangChain or Strands. |

---

# 8. Plan for Week 8

- Implement one working FR-12 assistant query from the dashboard through an approved FR-13 tool.
- Implement FR-14 and NFR-06 together so no write-capable agent tool can bypass approval or allowlisting.
- Add NFR-07 structured tool-attempt logging with sanitized evidence.
- Incorporate instructor feedback on the SAC and groom ML implementation stories without starting unapproved scope.
- Continue focused tests and full CI after each story slice.

---

# 9. Overall Sprint Assessment

Sprint 3 is on track. Nine of 22 story points are Done, representing 40.9% completion in the first reporting week. The completed work establishes a live UI-to-FastAPI workflow action, a controlled read-only agent-tool boundary, and an instructor-ready significant algorithmic component proposal. Thirteen points remain across assistant queries, approval-gated actions, operation restrictions, and audit logging. The next priority is a complete FR-12 read-only assistant slice followed by the coupled FR-14/NFR-06 security boundary.
