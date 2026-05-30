# SentinelOps Weekly Progress Report

> Sample report only. This file previews the weekly report format before Sprint 1 begins and should not be treated as a submitted sprint progress report.

## Report Information

| Field | Value |
|---|---|
| Course | SWENG 894 - Software Engineering Capstone Experience |
| Project | SentinelOps |
| Sprint | Pre-Sprint / Planning |
| Reporting Week | Week 0 Sample |
| Reporting Window | 2026-05-11 to 2026-05-17 |
| Student | Eli Vazquez |
| Report Date | 2026-05-17 |
| Repository | SentinelOps GitHub repository |
| Jira Board | https://psu-capstone-sentinelops.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog |

## Sprint Goal

Sprint 1 has not started yet. The intended Sprint 1 goal is to establish the project foundation for the first predictive maintenance workflow: telemetry generation, raw data storage, initial feature processing, and Airflow-based orchestration.

The practical objective is to produce a small but traceable vertical slice that can be expanded in later sprints without forcing a redesign of the API, Spark processing, or orchestration boundaries.

## Sprint Planning

### Sprint Backlog

| ID | Requirement / User Story | Priority | Estimate | Status |
|---|---|---|---|---|
| FR-01 | Telemetry Generation and Ingestion | High | 5 SP | Planned |
| FR-02 | Raw Telemetry Storage | High | 3 SP | Planned |
| FR-03 | Feature Engineering Processing | High | 5 SP | Planned |
| FR-04 | Workflow Orchestration | High | 8 SP | Planned |
| NFR-01 | Failed Workflow Detection and Reporting | High | Not estimated | Planned |
| NFR-03 | Component Responsibility Separation | High | Not estimated | Planned |
| NFR-04 | Repeatable Local Execution | Medium | Not estimated | Planned |

### Product Backlog Updates

The functional and non-functional requirements have been documented and loaded into Jira. Sprint assignments have been created for four planned sprints, with Sprint 1 focused on telemetry, storage, feature processing, and orchestration foundations.

No implementation-driven backlog changes have occurred yet because the sprint has not started.

### Definition of Done

| Area | Definition of Done Criteria |
|---|---|
| Requirements | Acceptance criteria reviewed and updated when implementation clarifies behavior |
| Design | Architecture notes updated when component boundaries change |
| Development | Source code implemented, committed, and traceable to a requirement |
| Testing | Practical validation added for implemented behavior |
| Documentation | Relevant setup, architecture, or usage documentation updated |
| Integration | Changes run locally through the intended workflow where feasible |
| Review | Work checked against acceptance criteria before marking complete |

## Acceptance Criteria Review

### FR-01 - Telemetry Generation and Ingestion

| Given | When | Then |
|---|---|---|
| The telemetry simulator is configured | A telemetry generation workflow is executed | Representative telemetry data is produced and available for processing |

### FR-02 - Raw Telemetry Storage

| Given | When | Then |
|---|---|---|
| Telemetry data is generated or ingested | The ingestion workflow completes | Raw telemetry data is persisted in the configured storage location |

### FR-03 - Feature Engineering Processing

| Given | When | Then |
|---|---|---|
| Raw telemetry data exists | The feature engineering workflow executes | Processed feature sets are generated and stored for predictive scoring |

### FR-04 - Workflow Orchestration

| Given | When | Then |
|---|---|---|
| Workflow definitions are configured | A workflow is triggered | Telemetry ingestion, processing, scoring, and reporting tasks execute in the defined sequence |

## Source Code Development

### Summary of Contributions

This sample report reflects planning work rather than sprint implementation. Current progress includes documentation structure cleanup, requirements documentation, architecture documentation, Jira backlog creation, and sprint assignment.

No Sprint 1 source-code work is reported here because the sprint has not started.

### Repository Information

| Resource | Link |
|---|---|
| Git Repository | SentinelOps GitHub repository |
| Jira Board | https://psu-capstone-sentinelops.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog |
| Sprint Board | Jira board Sprint 1 view |

### Important Commits

| Commit ID | Description | Related Requirement |
|---|---|---|
| cca5e69 | Merge project conception and documentation updates | Documentation |
| 5a815f0 | Complete project conception documentation | Documentation |
| fa618ec | Initialize project structure and CONOPS documentation | Documentation |

## Burndown Status

Sprint 1 has not started, so no burndown trend is available yet. The initial sprint backlog contains 21 functional story points plus supporting non-functional requirements related to reliability, maintainability, and local execution.

Once Sprint 1 begins, this section should summarize completed points, remaining points, scope changes, and any delivery risk observed during the reporting window.

## Burndown Chart

No burndown chart is included in this sample because Sprint 1 has not started.

## Software Testing

### Testing Overview

No implementation tests are reported for this pre-sprint sample. Early Sprint 1 testing should focus on validating telemetry generation, persistence, feature processing, and workflow execution behavior.

### Requirement-to-Test Mapping

| Requirement ID | Test Case ID | Test Description | Status |
|---|---|---|---|
| FR-01 | TC-01 | Validate telemetry generation produces representative asset telemetry | Planned |
| FR-02 | TC-02 | Validate raw telemetry is persisted after ingestion | Planned |
| FR-03 | TC-03 | Validate feature processing creates structured feature output | Planned |
| FR-04 | TC-04 | Validate Airflow workflow executes tasks in the expected sequence | Planned |
| NFR-04 | TC-05 | Validate the local setup can be repeated from documented instructions | Planned |

### Test Case Specifications

#### TC-01 - Validate Telemetry Generation

| Field | Description |
|---|---|
| Related Requirement | FR-01 |
| Preconditions | Telemetry simulator configuration exists |
| Test Steps | Execute the simulator or telemetry generation workflow |
| Expected Result | Representative telemetry records are generated for sample assets |
| Status | Planned |

#### TC-04 - Validate Workflow Orchestration

| Field | Description |
|---|---|
| Related Requirement | FR-04 |
| Preconditions | Airflow DAG and local services are configured |
| Test Steps | Trigger the predictive maintenance workflow |
| Expected Result | Workflow tasks execute in the documented sequence and expose execution status |
| Status | Planned |

## Risks and Roadblocks

- Airflow and Spark integration should be kept intentionally small in Sprint 1 so the first workflow remains demonstrable.
- The data model for telemetry and processed features may need adjustment after the first implementation pass.
- Test scope should stay tied to implemented behavior to avoid creating brittle placeholder tests.

## Planned Activities for Next Week

- Confirm Sprint 1 backlog readiness in Jira.
- Start the telemetry simulator implementation.
- Define the first raw telemetry storage format.
- Create the initial feature-processing path.
- Draft the first Airflow DAG for the telemetry processing workflow.
- Add practical validation for the first implemented workflow steps.

## Overall Sprint Assessment

The project is ready to enter Sprint 1 planning with a clear backlog and traceable requirements. The highest near-term risk is integration complexity, so the first sprint should prioritize a small end-to-end workflow over broad feature coverage.
