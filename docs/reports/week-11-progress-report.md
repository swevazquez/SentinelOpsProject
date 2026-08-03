# SentinelOps Weekly Progress Report

# 1. Report Metadata

| Field | Value |
|---|---|
| Course | SWENG 894 - Software Engineering Capstone Experience |
| Project | SentinelOps |
| Student | Eli Vazquez |
| Sprint | Sprint 4 |
| Reporting Week | Week 11 |
| Reporting Period | 2026-08-03 to 2026-08-09 |
| Report Date | 2026-08-03 |
| Report Status | Current through 2026-08-03 |
| Git Repository | <https://github.com/swevazquez/SentinelOpsProject> |
| Jira Board | <https://psu-capstone-sentinelops.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog> |

---

# 2. Sprint Goal and Status

Sprint 4 completes the integrated predictive-maintenance MVP. The sprint goal is to run versioned Random Forest Remaining Useful Life (RUL) inference through Spark and Airflow, persist operational results in PostgreSQL, expose the results through FastAPI and the dashboard, and provide one reproducible Docker Compose deployment.

The integrated product path is now complete. All seven implementation stories are Done, representing 41 of 46 committed story points. The remaining five-point documentation story will use the final course time for required documentation and demonstration preparation.

| Order | Jira | Sprint Outcome | Priority | Estimate | Status |
|---:|---|---|---|---:|---|
| 1 | SCRUM-31 | Train and evaluate the Random Forest RUL model. | Highest | 8 SP | Done |
| 2 | SCRUM-32 | Integrate versioned RUL inference with workflows and APIs. | Highest | 8 SP | Done |
| 3 | SCRUM-33 | Present and explain RUL results through the dashboard and Assistant. | Highest | 5 SP | Done |
| 4 | SCRUM-36 | Persist predictions and workflow state in PostgreSQL. | High | 5 SP | Done |
| 5 | SCRUM-37 | Run feature preparation and batch RUL scoring through Spark. | High | 5 SP | Done |
| 6 | SCRUM-35 | Coordinate the final predictive-maintenance workflow through Airflow. | High | 5 SP | Done |
| 7 | SCRUM-34 | Start and validate the integrated application through Docker Compose. | High | 5 SP | Done |
| 8 | SCRUM-26 | Complete readable final project documentation and demonstration guidance. | Medium | 5 SP | Remaining |

## Requirement and Acceptance Summary

| Jira | Requirement | Acceptance Criteria |
|---|---|---|
| SCRUM-31 | Repeatable Random Forest training and evaluation | Training produces a versioned RUL model, reports model and baseline metrics, preserves engine-isolated partitions, and rejects incompatible data. |
| SCRUM-32 | Versioned RUL workflow integration | Compatible trajectories produce nonnegative, traceable RUL results and maintenance classifications; invalid artifacts fail without corrupting stored results. |
| SCRUM-33 | User-facing RUL results and explanation | The dashboard and Assistant show grounded RUL values, model evidence, recommendations, and clear unavailable states without confusing RUL with risk. |
| SCRUM-36 | Durable operational persistence | Predictions and workflow state persist in PostgreSQL across restart with traceability and explicit unavailable-database failures; file mode remains usable. |
| SCRUM-37 | Spark batch RUL processing | Spark validates compatible input, prepares a typed batch, invokes versioned inference, persists results through the shared interface, and fails safely. |
| SCRUM-35 | Final Airflow orchestration | The DAG loads, executes the Spark workflow in order, records terminal status, and makes completed results available through FastAPI. |
| SCRUM-34 | Integrated Compose deployment | One documented Compose command starts the real API/dashboard, PostgreSQL, Airflow, and Spark runtime with observable health checks. |
| SCRUM-26 | Final documentation and demonstration readiness | Required documentation is consistent with the delivered system, reviewer-readable, traceable, and sufficient to install, evaluate, and demonstrate the MVP. |

---

# 3. Implemented UI Design and Sprint Alignment

The evidence below uses the current application running through the integrated Docker Compose stack. These are implemented product screenshots rather than planning wireframes. Together they show how the maintenance manager moves from fleet status to asset evidence, workflow execution, and controlled Assistant support.

## Fleet Overview

The Overview provides the main operational hierarchy: fleet condition, active alerts, workflow reliability, RUL distribution, recent Airflow runs, and the assets requiring attention. It lets the maintenance manager identify the shortest maintenance horizons without inspecting infrastructure services.

![Implemented Fleet Overview](../images/reports/week-11-ui/overview.png)

## Asset Health and Prediction Detail

The Assets view sorts the four demonstration engines by RUL and presents risk, condition, priority, and recommended action together. Opening an asset exposes the Random Forest result, model version, C-MAPSS dataset, prediction time, workflow run, and feature contract. This design keeps a predicted maintenance horizon distinct from the risk score and provides evidence for the recommendation.

![Implemented Asset Health View](../images/reports/week-11-ui/assets.png)

![Implemented Asset Prediction Detail](../images/reports/week-11-ui/asset-details.png)

## Workflow Execution

The Workflows view supports the repeatable four-checkpoint demonstration. It shows the next available checkpoint, completed and failed counts, Airflow execution history, and the most recent pipeline timeline from queued request through held-out C-MAPSS replay, Random Forest inference, and result publication. Controls become available after a run finishes, allowing the next checkpoint or a reset without a page refresh.

![Implemented Workflow Execution View](../images/reports/week-11-ui/workflows.png)

## Operations Assistant

The Assistant provides grounded operational queries using approved tools and current asset and workflow context. Informational questions are read-only. Operational workflow requests remain approval-gated so the user can review the proposed action before execution.

![Implemented Operations Assistant](../images/reports/week-11-ui/assistant.png)

## UI-to-Sprint Traceability

| Sprint Story | Implemented UI Evidence | Alignment |
|---|---|---|
| SCRUM-31 | Asset Prediction Detail | Displays the trained model name, version, dataset, prediction type, and supporting metadata. Model training is a backend responsibility and does not require a separate user screen. |
| SCRUM-32 | Asset Health, Asset Prediction Detail, Workflow Execution | Demonstrates that versioned RUL inference reaches stored asset results and remains traceable to a workflow run. |
| SCRUM-33 | Fleet Overview, Asset Health, Asset Prediction Detail, Assistant | Provides the complete user-facing RUL result, explanation, recommendation, and grounded Assistant experience. |
| SCRUM-36 | Fleet Overview, Asset Health, Workflow Execution | Shows operational predictions and workflow history returned from PostgreSQL. Database administration is intentionally not exposed to the maintenance manager. |
| SCRUM-37 | Workflow Execution, Asset Prediction Detail | The pipeline timeline identifies the batch inference stage and the resulting prediction evidence. Spark internals remain an implementation boundary rather than a user screen. |
| SCRUM-35 | Workflow Execution, Fleet Overview | Shows Airflow-coordinated execution, terminal status, pipeline order, and results reflected in the operational dashboard. |
| SCRUM-34 | All five views | The complete interface is served by the real FastAPI application through the integrated Compose deployment. Service readiness is verified through system tests rather than a deployment screen. |
| SCRUM-26 | All five views | These current screens are the user-facing evidence to be incorporated into the final documentation and demonstration guidance. |

All user-facing Sprint 4 requirements have implemented visual evidence. PostgreSQL schemas, Spark execution internals, Airflow service administration, and container health are technical boundaries, so separate maintenance-manager screens would not improve the workflow. Their acceptance is covered by the tests below.

---

# 4. Software Testing

## Test Approach and Results

Testing combines unit tests for model and component behavior, integration tests across persistence and orchestration boundaries, system tests for Spark and Compose execution, and user-acceptance review of the implemented workflow. The validated baseline contains 170 automated tests, with four environment-dependent tests skipped when their external service is not configured. The repository smoke workflow, Airflow DAG syntax, Markdown readability, and Docker Compose configuration also pass.

The full regression command is:

```bash
UV_CACHE_DIR=/tmp/sentinelops-uv-cache uv run --extra spark ./scripts/check-ci.sh
```

One non-blocking Starlette `TestClient` deprecation warning remains. Expected error log messages exercise controlled failure paths and are not test failures.

## Requirement-to-Test Traceability Matrix

| Jira | Test Case | Type | Requirement Covered | Status |
|---|---|---|---|---|
| SCRUM-31 | TC-S4-31 | Unit | Repeatable training, evaluation, versioned metadata, invalid input | Passed |
| SCRUM-32 | TC-S4-32 | Unit / Integration | RUL inference, classification, persistence, API traceability, safe failure | Passed |
| SCRUM-33 | TC-S4-33 | Unit / E2E / UAT | Dashboard and Assistant explanation, unavailable states, repeatable demo | Passed |
| SCRUM-36 | TC-S4-36 | Unit / Integration | PostgreSQL configuration, persistence, restart recovery, explicit failure | Passed |
| SCRUM-37 | TC-S4-37 | Unit / Integration / System | Spark validation, batch scoring, shared persistence, CLI behavior | Passed |
| SCRUM-35 | TC-S4-35 | Unit / Integration / UAT | Airflow DAG order, API submission, state synchronization, result retrieval | Passed |
| SCRUM-34 | TC-S4-34 | Integration / System / UAT | Compose configuration, startup, health, integrated dashboard, shutdown | Passed |
| SCRUM-26 | TC-S4-26 | Documentation Review / UAT | Final-document accuracy, traceability, setup, workflows, and readability | Planned |

## Test Case Specifications

Commands begin at the repository root.

### TC-S4-31 - Random Forest RUL Training

| Field | Specification |
|---|---|
| Preconditions | Project dependencies and prepared FD001 training partitions are available. |
| Action | Run `uv run pytest -q tests/unit/test_rul_training.py`, then run the full regression command. |
| Expected | Seeded training is repeatable; engines do not cross data partitions; model and baseline metrics plus versioned metadata are recorded; incompatible data produces no artifact. |
| Actual | Focused and regression tests passed. |
| Evidence | [`tests/unit/test_rul_training.py`](../../tests/unit/test_rul_training.py) and [PR #28](https://github.com/swevazquez/SentinelOpsProject/pull/28). |
| Cleanup | Test fixtures remove temporary artifacts. |

### TC-S4-32 - RUL Workflow Integration

| Field | Specification |
|---|---|
| Preconditions | Tests can create isolated model, workflow, and prediction repositories. |
| Action | Run `uv run pytest -q tests/unit/test_rul_inference.py tests/integration/test_manual_workflow_api.py`, then run the full regression command. |
| Expected | Valid trajectories produce nonnegative traceable RUL and maintenance terms; APIs return stored results; corrupt input records failure without changing previous predictions. |
| Actual | Focused and regression tests passed. |
| Evidence | [`tests/unit/test_rul_inference.py`](../../tests/unit/test_rul_inference.py), [`tests/integration/test_manual_workflow_api.py`](../../tests/integration/test_manual_workflow_api.py), and [PR #29](https://github.com/swevazquez/SentinelOpsProject/pull/29). |
| Cleanup | Test fixtures remove isolated repositories and artifacts. |

### TC-S4-33 - RUL Results and Explanation

| Field | Specification |
|---|---|
| Preconditions | Automated tests use isolated state; UAT uses the prepared model and running application. |
| Action | Run `uv run pytest -q tests/e2e/test_rul_experience.py tests/unit/test_rul_demo.py tests/unit/test_dashboard_ui.py tests/unit/test_agent_assistant.py`. In the UI, execute the four checkpoints, inspect asset details and Assistant evidence, then reset. |
| Expected | RUL reaches the API, dashboard, and Assistant; results are grounded and distinguish RUL from risk; unavailable values are not fabricated; reset restores the repeatable demonstration. |
| Actual | Automated tests passed and the current UI was reviewed through all five report screenshots. |
| Evidence | [`tests/e2e/test_rul_experience.py`](../../tests/e2e/test_rul_experience.py), [`tests/unit/test_rul_demo.py`](../../tests/unit/test_rul_demo.py), [PR #30](https://github.com/swevazquez/SentinelOpsProject/pull/30), and the screenshots in Section 3. |
| Cleanup | Use **Reset demo** after UAT. |

### TC-S4-36 - PostgreSQL Persistence

| Field | Specification |
|---|---|
| Preconditions | PostgreSQL is available and an isolated database URL is supplied for live integration. |
| Action | Run `uv run pytest -q tests/unit/test_persistence_config.py`. Then run `SENTINELOPS_TEST_DATABASE_URL=postgresql://sentinelops:sentinelops@127.0.0.1:5432/sentinelops uv run pytest -q tests/integration/test_postgres_persistence.py`. Restart the API and retrieve the stored workflow and predictions. |
| Expected | Configuration selects the requested backend; predictions and workflows survive restart with traceability; unavailable PostgreSQL returns an explicit error; file mode remains operational. |
| Actual | Unit and live PostgreSQL integration tests passed. Environment-gated database tests skip only when the database URL is absent. |
| Evidence | [`tests/unit/test_persistence_config.py`](../../tests/unit/test_persistence_config.py), [`tests/integration/test_postgres_persistence.py`](../../tests/integration/test_postgres_persistence.py), and [PR #31](https://github.com/swevazquez/SentinelOpsProject/pull/31). |
| Cleanup | Remove test rows or stop the isolated database after verification. |

### TC-S4-37 - Spark Batch Processing

| Field | Specification |
|---|---|
| Preconditions | Java, Spark dependencies, prepared FD001 input, and the versioned RUL artifact are available. |
| Action | Run `uv run --extra spark pytest -q tests/unit/test_spark_rul_batch.py tests/integration/test_spark_rul_batch.py tests/system/test_spark_cli.py`, then run the full regression command. |
| Expected | Spark validates and types compatible input, executes batch RUL scoring, preserves model and run traceability, writes through the shared repository, and returns nonzero for invalid input. |
| Actual | Unit, integration, CLI system, and regression tests passed. |
| Evidence | [`tests/unit/test_spark_rul_batch.py`](../../tests/unit/test_spark_rul_batch.py), [`tests/integration/test_spark_rul_batch.py`](../../tests/integration/test_spark_rul_batch.py), [`tests/system/test_spark_cli.py`](../../tests/system/test_spark_cli.py), and [PR #32](https://github.com/swevazquez/SentinelOpsProject/pull/32). |
| Cleanup | Test fixtures remove temporary inputs, outputs, and repositories. |

### TC-S4-35 - Final Airflow Orchestration

| Field | Specification |
|---|---|
| Preconditions | The Airflow test harness is available; integrated UAT uses the Compose stack and prepared RUL assets. |
| Action | Run `uv run pytest -q tests/unit/test_airflow_pipeline.py tests/integration/test_airflow_pipeline.py tests/unit/test_airflow_client.py tests/integration/test_airflow_api.py`. In the UI, run successive checkpoints without refreshing and verify workflow and asset results. |
| Expected | The DAG loads with the correct task sequence; FastAPI submits to Airflow; terminal state releases the next control; success and failure are recorded; results are returned through the API. |
| Actual | Automated tests passed. UAT confirmed successive checkpoints and reset become available after terminal state without a refresh in Chrome. |
| Evidence | [`tests/unit/test_airflow_pipeline.py`](../../tests/unit/test_airflow_pipeline.py), [`tests/integration/test_airflow_pipeline.py`](../../tests/integration/test_airflow_pipeline.py), [`tests/integration/test_airflow_api.py`](../../tests/integration/test_airflow_api.py), [PR #33](https://github.com/swevazquez/SentinelOpsProject/pull/33), and the Workflow screenshot in Section 3. |
| Cleanup | Use **Reset demo** and stop the stack when review is complete. |

### TC-S4-34 - Integrated Docker Compose Deployment

| Field | Specification |
|---|---|
| Preconditions | Docker is running and required local configuration is present. |
| Action | Run `bash scripts/check-compose.sh config`, `docker compose up -d --build --wait`, `curl --fail http://127.0.0.1:8000/api/health`, and `docker compose ps`. Open the dashboard and complete one checkpoint. |
| Expected | API/dashboard, PostgreSQL, and Airflow report healthy; the Airflow-to-Spark-to-PostgreSQL path completes; the dashboard displays the result; invalid configuration fails clearly. |
| Actual | Twenty-two focused Compose tests passed, all services reached healthy state, the health endpoint responded, and the live application produced the Section 3 screenshots. |
| Evidence | [`tests/integration/test_api_health.py`](../../tests/integration/test_api_health.py), [`tests/system/test_compose_configuration.py`](../../tests/system/test_compose_configuration.py), [`scripts/check-compose.sh`](../../scripts/check-compose.sh), and [PR #34](https://github.com/swevazquez/SentinelOpsProject/pull/34). |
| Cleanup | Run `docker compose down` after review. |

### TC-S4-26 - Final Documentation Review

| Field | Specification |
|---|---|
| Preconditions | Final SRS, architecture and design document, testing report, end-user manual, root README, and demonstration guidance are available. |
| Action | From a clean checkout, follow the documented setup; execute every documented maintenance-manager workflow; run the full regression command; verify requirements, diagrams, test mappings, links, and screenshots against the application. |
| Expected | A reviewer can install, operate, test, and understand the delivered MVP without undocumented steps; all statements and visual evidence match implemented behavior. |
| Actual | Planned for the remaining sprint work. |
| Evidence | Final documentation sources and reviewer checklist will provide the acceptance record. |
| Cleanup | Reset the demonstration and stop all services. |

---

# 5. Source Code Development

## Summary of Recent Contributions

- Added PostgreSQL repositories for durable prediction and workflow state while retaining explicit file-backed development mode.
- Added local Spark validation, feature preparation, batch RUL inference, shared persistence, and CLI coverage.
- Completed the Airflow RUL DAG and routed the dashboard workflow through Airflow, Spark, PostgreSQL, and FastAPI.
- Synchronized workflow controls and Assistant configuration so terminal state is reflected without manual refresh.
- Added the integrated Docker Compose deployment, API readiness endpoint, service health checks, startup validation, and reviewer-facing setup instructions.

## Important Commits

| Commit | Contribution | Review Evidence |
|---|---|---|
| [`1ee2621`](https://github.com/swevazquez/SentinelOpsProject/commit/1ee262139dd9f0a95e694f41757c4afa8709772f) | Add PostgreSQL operational persistence. | [PR #31](https://github.com/swevazquez/SentinelOpsProject/pull/31) |
| [`8296a48`](https://github.com/swevazquez/SentinelOpsProject/commit/8296a487d82f9ca11854ceab69e46f448aa5f8d9) | Add local Spark RUL batch processing. | [PR #32](https://github.com/swevazquez/SentinelOpsProject/pull/32) |
| [`eecba6b`](https://github.com/swevazquez/SentinelOpsProject/commit/eecba6becc980ce48a95bcf9cd9c7b3c289b4f6b) | Add final Airflow RUL orchestration. | [PR #33](https://github.com/swevazquez/SentinelOpsProject/pull/33) |
| [`775b270`](https://github.com/swevazquez/SentinelOpsProject/commit/775b270eb3458642acc4872fa95fb01c1588293a) | Route the dashboard through the Airflow demo stack. | [PR #33](https://github.com/swevazquez/SentinelOpsProject/pull/33) |
| [`46de633`](https://github.com/swevazquez/SentinelOpsProject/commit/46de633e5cb38d7f6db93cd7a8c95a18cc3826f8), [`324ca27`](https://github.com/swevazquez/SentinelOpsProject/commit/324ca27efdc7071fcaaeb1d3107d2d92768d97c4) | Synchronize Assistant configuration and release controls after completed checkpoints. | [PR #33](https://github.com/swevazquez/SentinelOpsProject/pull/33) |
| [`50e4beb`](https://github.com/swevazquez/SentinelOpsProject/commit/50e4beb751f0e554dcb44475c5dcd14449545ef1) | Add Compose readiness validation and integrated deployment. | [PR #34](https://github.com/swevazquez/SentinelOpsProject/pull/34) |

## Burndown

| Metric | Value |
|---|---:|
| Planned Sprint Delivery | 46 story points |
| Completed | 41 story points |
| Remaining | 5 story points |
| Percent Complete | 89.1% |
| Sprint End | Week 12 |

The actual line shows 25 points remaining at Week 10 and five at Week 11. The final five points represent documentation and demonstration readiness, and the chart ends at the planned Week 12 sprint boundary.

![Sprint 4 Week 11 Burndown](../images/reports/week-11-burndown.svg)

---

# 6. Backlog Grooming

The product and sprint backlogs were reviewed after completion of the integrated MVP path. The review protected the final delivery goal and removed lower-priority expansion work from the active sprint.

| Change | Jira | Backlog Action | Rationale and Effect |
|---|---|---|---|
| Completed | SCRUM-36, SCRUM-37, SCRUM-35, SCRUM-34 | Moved through review to Done after their pull requests merged. | Completes PostgreSQL, Spark, Airflow, and Compose integration. The sprint now has 41 of 46 points Done. |
| Retained | SCRUM-26 | Remains the final five-point Sprint 4 item. | Reserves the remaining course time for required documentation and demonstration preparation. |
| Deferred | SCRUM-15, SCRUM-16, SCRUM-25 | Removed from the active sprint and retained as To Do in the product backlog. | These lower-priority enhancements are not required for the integrated MVP. Deferral prevents scope expansion from displacing final documentation and demo readiness. |

No new implementation scope was added. The reported Sprint 4 commitment remains 46 points because the deferred items were not part of the committed Week 10 scope.

---

# 7. Remaining Course Plan

The integrated MVP is available for evaluation. The remaining course time will be used to:

1. Complete and reconcile the required final software requirements, architecture and design, testing, and end-user documents against the delivered system.
2. Perform the documentation acceptance review from a clean setup path.
3. Rehearse the repeatable four-checkpoint demonstration and verify model, workflow, persistence, and Assistant evidence.
4. Prepare the final demonstration submission.

The principal remaining risk is demonstration-environment readiness: the prepared C-MAPSS data, trained model artifact, Docker services, and optional OpenAI Assistant configuration must be available together. The documented Compose setup, reset control, health endpoint, and rehearsal procedure reduce this risk.

---

# 8. Overall Assessment

Sprint 4 is 89.1% complete. SentinelOps now demonstrates the planned end-to-end architecture: Airflow coordinates a repeatable held-out C-MAPSS checkpoint, Spark executes the batch inference boundary, the versioned Random Forest model estimates RUL, PostgreSQL stores workflow and prediction evidence, FastAPI exposes the results, and the dashboard presents them to a maintenance manager. The remaining work is limited to final documentation, acceptance review, and demonstration preparation.
