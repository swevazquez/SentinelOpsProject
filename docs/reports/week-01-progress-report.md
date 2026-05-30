# SentinelOps Weekly Progress Report

| Field | Value |
|---|---|
| Course | SWENG 894 - Software Engineering Capstone Experience |
| Project | SentinelOps |
| Student | Eli Vazquez |
| Sprint | Sprint 1 |
| Reporting Week | Week 1 |
| Reporting Period | 2026-05-25 to 2026-05-31 |
| Report Date | 2026-05-30 |
| Git Repository | <https://github.com/swevazquez/SentinelOpsProject> |
| Jira Board | <https://psu-capstone-sentinelops.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog> |

---

# Sprint Goal

The Sprint 1 goal is to establish the first working SentinelOps foundation for a predictive maintenance workflow. The sprint focuses on representative telemetry generation, raw telemetry persistence, initial feature processing, and repeatable workflow validation.

This week focused on starting the sprint correctly by connecting Jira and GitHub traceability, implementing the first telemetry generation story, and pulling automated CI validation forward so later Sprint 1 work can be integrated safely.

---

# Sprint Planning

## Groomed Product Backlog Summary

The Sprint 1 backlog was reviewed in Jira and confirmed as the starting scope for the first vertical slice.

| ID | Requirement / User Story | Priority | Estimation | Sprint | Current Status |
|---|---|---|---|---|---|
| FR-01 | Telemetry Generation and Ingestion | High | 5 SP | Sprint 1 | In Progress |
| FR-02 | Raw Telemetry Storage | High | 3 SP | Sprint 1 | To Do |
| FR-03 | Feature Engineering Processing | High | 5 SP | Sprint 1 | To Do |
| FR-04 | Workflow Orchestration | High | 8 SP | Sprint 1 | To Do |
| NFR-01 | Failed Workflow Detection and Reporting | High | Not estimated | Sprint 1 | To Do |
| NFR-03 | Component Responsibility Separation | High | Not estimated | Sprint 1 | To Do |
| NFR-04 | Repeatable Local Execution | Medium | Not estimated | Sprint 1 | To Do |

## Sprint Backlog

| ID | Requirement / User Story | Priority | Estimation | Status |
|---|---|---|---|---|
| FR-01 | Telemetry Generation and Ingestion | High | 5 SP | In Progress |
| FR-02 | Raw Telemetry Storage | High | 3 SP | To Do |
| FR-03 | Feature Engineering Processing | High | 5 SP | To Do |
| FR-04 | Workflow Orchestration | High | 8 SP | To Do |
| NFR-01 | Failed Workflow Detection and Reporting | High | Not estimated | To Do |
| NFR-03 | Component Responsibility Separation | High | Not estimated | To Do |
| NFR-04 | Repeatable Local Execution | Medium | Not estimated | To Do |

## Definition of Done

| Area | Definition of Done Criteria |
|---|---|
| Requirements | Requirement is reviewed and acceptance criteria are documented. |
| Design | Affected architecture, workflow, or interface design is updated. |
| Development | Code is implemented, committed, and aligned with the existing project structure. |
| Testing | Unit, smoke, or manual validation is completed as appropriate. |
| Integration | Changes run through the local CI validation script and GitHub Actions. |
| Documentation | Relevant documentation and weekly reporting evidence are updated. |
| Validation | Implementation is validated against acceptance criteria. |

## Acceptance Criteria for Sprint Backlog Items

| Requirement ID | Acceptance Criteria |
|---|---|
| FR-01 | Given the telemetry simulator is configured, when a telemetry generation workflow is executed, then representative telemetry data shall be produced and made available for processing. |
| FR-02 | Given telemetry data is generated or ingested, when the ingestion workflow completes, then the telemetry data shall be persisted in the configured storage location. |
| FR-03 | Given raw telemetry data exists, when the feature engineering workflow executes, then processed feature sets shall be generated and stored for predictive scoring. |
| FR-04 | Given workflow definitions are configured, when a workflow is triggered, then telemetry ingestion, processing, scoring, and reporting tasks shall execute in the defined sequence. |

---

# Backlog Grooming

## Backlog Changes This Week

| Change Type | Requirement ID | Description | Rationale | Impact |
|---|---|---|---|---|
| Moved earlier | NFR-04 / NFR-09 | Automated CI validation was pulled forward into Sprint 1 planning. | Early telemetry, storage, feature, and workflow work needs repeatable verification before additional services are added. | Adds pipeline work to the first sprint foundation and provides testing evidence for weekly reporting. |

## Backlog Grooming Rationale

Automated testing and CI validation were pulled forward because the first sprint depends on several connected workflow steps. Establishing branch and pull-request validation now reduces integration risk before additional API, dashboard, prediction, and agent components are added. This supports repeatable local execution and creates concrete evidence for weekly reporting.

---

# Source Code Development

## Summary of Contributions

Development this week focused on project traceability, telemetry generation, and automated validation.

Key contributions include:

- Configured GitHub autolinks for Jira keys using the `SCRUM-` prefix.
- Added pull request traceability checks requiring Jira story keys.
- Added representative asset profile configuration for telemetry generation.
- Updated the simulator CLI to load and validate configured asset profiles.
- Added CI validation for unit tests, Sprint 1 smoke workflow output counts, Airflow DAG syntax, and documentation readability.

## Repository Information

| Resource | Link |
|---|---|
| Git Repository | <https://github.com/swevazquez/SentinelOpsProject> |
| Jira Board | <https://psu-capstone-sentinelops.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog> |
| Pull Request | <https://github.com/swevazquez/SentinelOpsProject/pull/1> |

## Important Commits

| Commit ID | Commit Summary | Related Requirement / User Story | Notes |
|---|---|---|---|
| 3196025 | Add Jira GitHub traceability workflow | NFR-04 | Establishes traceability and reporting support. |
| d2a174c | Configure telemetry asset generation | FR-01 | Adds configured representative telemetry input. |
| 74579b8 | Add CI validation pipeline | NFR-04 / NFR-09 | Adds local and GitHub Actions validation. |
| dfeb627 | Run CI on feature branch pushes | NFR-04 | Ensures branch work receives automated feedback before PR merge. |

## Burndown Summary

Sprint 1 is underway. `FR-01` is in progress and the project foundation now includes automated validation. Remaining work includes raw telemetry storage completion, feature engineering hardening, Airflow orchestration validation, and failure reporting behavior.

| Metric | Value |
|---|---|
| Sprint Total Estimated Effort | 21 functional story points plus supporting NFRs |
| Completed Effort | 0 story points formally completed |
| Remaining Effort | 21 functional story points plus supporting NFRs |
| Sprint Status | On Track |

## Burndown Chart

No burndown chart is included for this first weekly report.

---

# Software Testing

## Testing Overview

Automated testing was expanded and connected to CI. The project now has unit coverage for telemetry generation and asset profile validation, plus a smoke workflow that generates raw telemetry and processed features.

## Requirement-to-Test Traceability Matrix

| Requirement ID | Test Case ID | Test Type | Test Objective | Status |
|---|---|---|---|---|
| FR-01 | TC-FR01-01 | Unit | Validate telemetry generation creates hourly rows for each representative asset. | Passed |
| FR-01 | TC-FR01-02 | Unit | Validate asset profile configuration is loaded and used by telemetry generation. | Passed |
| FR-01 | TC-FR01-03 | Unit | Validate invalid asset risk configuration is rejected. | Passed |
| NFR-04 | TC-NFR04-01 | CI Smoke | Validate the Sprint 1 local workflow generates expected raw and processed outputs. | Passed |
| NFR-04 | TC-NFR04-02 | CI | Validate GitHub Actions runs on feature branch pushes and PRs. | Passed |

## Test Case Specifications

### TC-FR01-01 - Telemetry Generation Produces Representative Rows

| Field | Description |
|---|---|
| Related Requirement | FR-01 |
| Test Type | Unit |
| Preconditions | Telemetry simulator is configured with representative assets. |
| Test Steps | Run `python3 -m unittest discover -s tests`. |
| Expected Result | Telemetry rows are generated for each asset and hour with the expected fields. |
| Actual Result | Passed. |
| Status | Passed |

### TC-NFR04-01 - Sprint 1 CI Smoke Workflow

| Field | Description |
|---|---|
| Related Requirement | NFR-04 |
| Test Type | CI Smoke |
| Preconditions | Repository checkout and Python 3.12 are available. |
| Test Steps | Run `./scripts/check-ci.sh`. |
| Expected Result | Unit tests pass, smoke data is generated, expected output counts match, and DAG syntax is valid. |
| Actual Result | Passed locally and in GitHub Actions. |
| Status | Passed |

## Testing Summary

Local validation passed with `./scripts/check-ci.sh`. GitHub Actions also passed on the `SCRUM-1-telemetry-generation-ingestion` branch and PR #1.

---

# Risks, Roadblocks, and Mitigation

| Risk / Roadblock | Impact | Mitigation / Next Step |
|---|---|---|
| Sprint 1 spans several connected workflow steps. | Integration issues may appear when telemetry, storage, features, and orchestration are combined. | Keep CI smoke validation active and extend it as each Sprint 1 story lands. |

---

# Plan for Next Week

Next week’s work will focus on continuing the Sprint 1 vertical slice.

- Complete or merge the `SCRUM-1` telemetry generation work.
- Proceed to `SCRUM-2` raw telemetry storage.
- Expand validation evidence as storage and feature processing are refined.
- Keep Jira, GitHub PRs, commits, and weekly reports aligned.

---

# Overall Sprint Assessment

Sprint progress is currently on track. The first story is in progress, the codebase has a CI foundation, and the project now has stronger traceability between Jira, GitHub, tests, and weekly reporting. The main focus remains completing a small working vertical slice rather than expanding scope.
