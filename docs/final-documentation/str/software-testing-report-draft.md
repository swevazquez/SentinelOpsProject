# SentinelOps Software Testing Report

| Field | Value |
|---|---|
| Course | SWENG 894 - Software Engineering Capstone Experience |
| Project | SentinelOps |
| Author | Eli Vazquez |
| Document | Software Testing Report |
| Version | 1.0 |
| Date | August 8, 2026 |
| Repository | <https://github.com/swevazquez/SentinelOpsProject> |

## 1. Document Overview

### 1.1 Purpose

This report documents the testing practices used to develop SentinelOps and the evidence connecting tests to software requirements. It describes test specifications, implementations, execution procedures, results, testing progress, coverage, defects, continuous integration, and remaining quality risks.

### 1.2 Scope

The final test scope covers:

- telemetry generation and raw storage;
- feature engineering;
- workflow orchestration and status;
- predictive risk scoring and prediction persistence;
- API operations and request validation;
- dashboard contracts and user workflows;
- Assistant tool selection and grounded output;
- action restrictions, approvals, audit evidence, and replay protection;
- C-MAPSS FD001 parsing, labeling, partitioning, and metadata;
- Random Forest temporal features, training reproducibility, baseline comparison, and artifact metadata;
- versioned RUL inference, maintenance mapping, persistence, and safe failure;
- repeatable four-checkpoint RUL behavior and reset;
- RUL API, dashboard, notification, and grounded Assistant behavior;
- PostgreSQL repository selection, transactional replacement, restart retrieval, and unavailable-state behavior;
- Spark C-MAPSS validation, batch scoring, traceability, persistence, and CLI behavior;
- final Airflow DAG loading, task order, API trigger, success, callback, and failure behavior;
- Docker Compose configuration, service health, API readiness, and deployment behavior;
- clean-checkout behavior;
- demonstration-scale performance;
- architecture dependency rules;
- repository safeguards and Markdown readability.

The final integrated deployment path is verified through focused infrastructure tests and live Compose review. The host-only file-backed path remains a supported development and test mode.

### 1.3 Quality Objectives

Testing is intended to demonstrate that:

1. implemented requirements satisfy their acceptance criteria;
2. invalid or unsafe inputs fail before corrupting operational data;
3. workflow and prediction outputs remain traceable;
4. AI-assisted operations cannot bypass approved tools or explicit approval;
5. application layers integrate through a repeatable local and CI pipeline;
6. user-facing behavior remains understandable at supported viewport sizes;
7. known limitations and warnings are visible rather than hidden.

## 2. Testing Approach

### 2.1 Strategy

SentinelOps uses focused tests first and full regression afterward. Pure transformation and policy behavior is tested at unit level. API and cross-component behavior is tested through integration cases. Complete setup, performance, architecture, and workflow behavior is tested at system level. User-visible interactions receive browser-based user acceptance review.

Negative-path testing is especially important for:

- missing, malformed, or mixed-run data;
- failed workflow stages;
- unavailable or invalid stored artifacts;
- unknown tools and unexpected arguments;
- unapproved, denied, expired, modified, or replayed actions;
- Assistant provider failures;
- responsive-layout and navigation regressions.

### 2.2 Required and Supporting Test Types

| Type | Role in Quality Evidence | Automation |
|---|---|---|
| Unit | Verifies individual modules, policies, repositories, and transformations. | Automated |
| Integration | Verifies API-to-service, workflow-to-storage, Assistant-to-tool, and approval-to-execution boundaries. | Automated |
| System | Verifies clean setup, complete workflow behavior, performance, and repository-wide validation. | Automated |
| Architecture | Verifies component dependency rules. | Automated |
| Security | Verifies closed schemas, allowlists, sanitization, approval, exact match, and replay prevention. | Automated |
| Regression | Re-runs the complete implemented baseline. | Automated |
| User Acceptance | Verifies dashboard and Assistant workflows from the user's perspective. | Manual plus UI contract tests |
| Document Review | Verifies requirements and algorithm artifacts against instructor criteria. | Manual |

### 2.3 Tools

| Tool | Purpose |
|---|---|
| Python `unittest` | Primary repository-wide test discovery used by `scripts/check-ci.sh` |
| pytest | Focused execution and concise grouping by test directory |
| FastAPI TestClient / HTTPX | API integration and response-contract testing |
| Fake OpenAI Responses client | Deterministic Assistant tests without network access or API keys |
| Temporary directories | Isolated file-backed repository, workflow, approval, audit, and model-data tests |
| Standard-library `trace` | Statement coverage without adding a project dependency |
| GitHub Actions | Automated validation on pushes and pull requests |
| Browser inspection | Desktop/tablet UAT, console review, navigation, dialogs, and Assistant behavior |
| Shell validation scripts | Prerequisites, setup, CI, performance, workflow smoke, and Jira traceability |

### 2.4 Environment and Test Data

| Item | Final Configuration |
|---|---|
| Final verification date | August 8, 2026 |
| Python | 3.12 |
| Local dependency manager | `uv` |
| Local integrated runtime | macOS, Java 22, Docker Engine 28.3.3, Docker Compose 2.39.2 |
| CI operating system | GitHub-hosted Ubuntu |
| Dashboard UAT | 1248x720 desktop and 900x1000 tablet |
| Representative assets | `data/samples/asset_profiles.csv` |
| Workflow data | Deterministic 24-hour, four-asset telemetry |
| C-MAPSS CI data | Committed representative FD001 fixture |
| External model | Replaced by fake client in automated tests |

### 2.5 Entry and Exit Criteria

Entry criteria:

- requirement and acceptance criteria are defined;
- affected interfaces and expected failure behavior are understood;
- required fixture data is available;
- the branch includes the relevant implementation.

Exit criteria:

- focused tests pass;
- full validation passes;
- user-facing changes pass UAT;
- failures and warnings are documented;
- requirement traceability is current;
- no generated runtime data is accidentally tracked.

## 3. Test Specifications

### 3.1 Unit Test Specifications

#### TC-UNIT-DATA-01 - Telemetry and Feature Processing

| Field | Specification |
|---|---|
| Requirements | FR-01, FR-02, FR-03 |
| Acceptance Criteria | Valid profiles produce deterministic telemetry; valid runs persist; feature processing produces one record per asset; empty, malformed, mixed-run, or missing input fails. |
| Objective | Verify acquisition, raw persistence, transformation, validation, and run traceability. |
| Preconditions | Sample asset profiles and temporary raw/processed storage. |
| Test Data | Four valid profiles, invalid risk/profile values, empty input, mixed run IDs, and malformed rows. |
| Implementation | [`test_telemetry.py`](../../../tests/unit/test_telemetry.py), [`test_features.py`](../../../tests/unit/test_features.py) |
| Execution | `uv run pytest -q tests/unit/test_telemetry.py tests/unit/test_features.py` |
| Expected Result | All success, boundary, persistence, and rejection cases pass. |
| Result | Passed as part of the 127-test unit collection. |

#### TC-UNIT-PRED-01 - Scoring, Indicators, Storage, and Traceability

| Field | Specification |
|---|---|
| Requirements | FR-06, FR-07, FR-08, NFR-02 |
| Acceptance Criteria | Valid features produce bounded scores and maintenance fields; one prediction per asset is stored; each result retains run, source path, source fingerprint, model name, and version. |
| Objective | Verify deterministic prediction behavior and repository contracts. |
| Preconditions | Valid feature rows and temporary prediction storage. |
| Test Data | Threshold boundaries, invalid/missing fields, duplicate assets, mixed runs, invalid hashes, and retrieval ordering. |
| Implementation | [`test_scoring.py`](../../../tests/unit/test_scoring.py), [`test_prediction_store.py`](../../../tests/unit/test_prediction_store.py) |
| Execution | `uv run pytest -q tests/unit/test_scoring.py tests/unit/test_prediction_store.py` |
| Expected Result | Valid results and every documented validation path pass. |
| Result | Passed. |

#### TC-UNIT-OPS-01 - Workflow Status and API Operations

| Field | Specification |
|---|---|
| Requirements | FR-05, FR-09, NFR-01, NFR-05 |
| Acceptance Criteria | Running/completed/failed states are stored and retrieved; API operations return consistent success, validation, missing, and unavailable states. |
| Objective | Verify operational status, failure visibility, and response contracts. |
| Implementation | [`test_workflow_status.py`](../../../tests/unit/test_workflow_status.py), [`test_airflow_failure_reporting.py`](../../../tests/unit/test_airflow_failure_reporting.py), [`test_api_operations.py`](../../../tests/unit/test_api_operations.py) |
| Execution | `uv run pytest -q tests/unit/test_workflow_status.py tests/unit/test_airflow_failure_reporting.py tests/unit/test_api_operations.py` |
| Expected Result | Status, summary, failure, file-safety, and response-state cases pass. |
| Result | Passed. |

#### TC-UNIT-AGENT-01 - Controlled Assistant Operations

| Field | Specification |
|---|---|
| Requirements | FR-12, FR-13, FR-14, FR-15, NFR-06, NFR-07 |
| Acceptance Criteria | Supported queries use approved tools; unknown tools and malformed arguments fail; actions require a current exact approval; denied, expired, changed, or replayed requests write no workflow; audit evidence is sanitized. |
| Objective | Verify the complete AI safety and observability boundary. |
| Preconditions | Fake OpenAI client and temporary operational, approval, workflow, and audit data. |
| Implementation | [`test_agent_assistant.py`](../../../tests/unit/test_agent_assistant.py), [`test_agent_tools.py`](../../../tests/unit/test_agent_tools.py), [`test_agent_actions.py`](../../../tests/unit/test_agent_actions.py), [`test_agent_approvals.py`](../../../tests/unit/test_agent_approvals.py), [`test_agent_audit.py`](../../../tests/unit/test_agent_audit.py) |
| Execution | `uv run pytest -q tests/unit/test_agent_assistant.py tests/unit/test_agent_tools.py tests/unit/test_agent_actions.py tests/unit/test_agent_approvals.py tests/unit/test_agent_audit.py` |
| Expected Result | Query, tool, action, approval, failure, sanitization, and replay cases pass. |
| Result | Passed. |

#### TC-UNIT-SAC-01 - C-MAPSS FD001 Contract

| Field | Specification |
|---|---|
| Requirements | Implemented SAC data-contract foundation |
| Acceptance Criteria | Validate 26-column records, calculate uncapped and capped RUL, split by engine ID with a fixed seed, preserve checksums and metadata, and reject invalid records. |
| Objective | Verify the reproducible input and labeling contract for Random Forest RUL model work. |
| Implementation | [`test_cmapss.py`](../../../tests/unit/test_cmapss.py) |
| Execution | `uv run pytest -q tests/unit/test_cmapss.py` |
| Expected Result | Parser, labels, partitions, metadata, acquisition checks, and failures pass. |
| Result | Passed. |

#### TC-UNIT-RUL-01 - Random Forest Training and RUL Inference

| Field | Specification |
|---|---|
| Requirements | FR-RUL-02, FR-RUL-03, NFR-01 through NFR-03 |
| Acceptance Criteria | Training uses engine-isolated data and training-only preprocessing; repeated runs match; metrics and versioned metadata are complete; compatible trajectories produce bounded traceable results; invalid artifacts fail safely. |
| Objective | Verify the trained model contract and its reuse during runtime inference. |
| Preconditions | Representative FD001 fixture, temporary partitions, artifact directory, and prediction repository. |
| Implementation | [`test_rul_training.py`](../../../tests/unit/test_rul_training.py), [`test_rul_inference.py`](../../../tests/unit/test_rul_inference.py), [`test_rul_demo.py`](../../../tests/unit/test_rul_demo.py) |
| Execution | `uv run pytest -q tests/unit/test_rul_training.py tests/unit/test_rul_inference.py tests/unit/test_rul_demo.py` |
| Expected Result | Feature isolation, repeatability, artifact contents, inference, maintenance mapping, checkpoint progression, retry, history, reset, and failure cases pass. |
| Result | Passed. |

### 3.2 System Test Specifications

#### TC-SYS-WORKFLOW-01 - Integrated Predictive Workflow

| Field | Specification |
|---|---|
| Requirements | FR-04, FR-05, FR-06 through FR-09, FR-11 |
| Acceptance Criteria | One request generates raw telemetry, features, predictions, and traceable completed status; invalid requests create no workflow. |
| Preconditions | Repository root, sample profiles, Python dependencies, and temporary or local data directories. |
| Implementation | [`test_sprint1_workflow.py`](../../../tests/integration/test_sprint1_workflow.py), [`test_predictive_scoring.py`](../../../tests/integration/test_predictive_scoring.py), [`test_manual_workflow_api.py`](../../../tests/integration/test_manual_workflow_api.py) |
| Execution | `uv run pytest -q tests/integration/test_sprint1_workflow.py tests/integration/test_predictive_scoring.py tests/integration/test_manual_workflow_api.py` |
| Expected Result | Valid completion, persistence, traceability, API status, and failure cases pass. |
| Result | Passed as part of the 32-test integration collection. |

#### TC-SYS-RUL-01 - End-to-End RUL Experience

| Field | Specification |
|---|---|
| Requirements | FR-RUL-03 through FR-RUL-06, NFR-01, NFR-02, NFR-05, and NFR-09 |
| Acceptance Criteria | A compatible trajectory reaches inference, persistence, API, dashboard, and Assistant contracts; unavailable data is not replaced; active findings accumulate and can be acknowledged or cleared. |
| Preconditions | Isolated trained model, API application, demo state, prediction store, and fake Assistant client. |
| Implementation | [`test_rul_experience.py`](../../../tests/e2e/test_rul_experience.py), [`test_manual_workflow_api.py`](../../../tests/integration/test_manual_workflow_api.py), [`test_dashboard_ui.py`](../../../tests/unit/test_dashboard_ui.py) |
| Execution | `uv run pytest -q tests/e2e/test_rul_experience.py tests/integration/test_manual_workflow_api.py tests/unit/test_dashboard_ui.py` |
| Expected Result | RUL remains traceable and separate from risk across every interface, and repeatable demonstration and notification behavior pass. |
| Result | Passed. |

#### TC-INFRA-36 - PostgreSQL Operational Persistence

| Field | Specification |
|---|---|
| Requirements | FR-08, FR-17, NFR-02, NFR-05 |
| Acceptance Criteria | Selecting PostgreSQL stores predictions and workflow state durably, a new API instance retrieves the same records, replacement is transactional, and an unavailable database returns an explicit response without silent file fallback. |
| Preconditions | Docker PostgreSQL is healthy and `SENTINELOPS_TEST_DATABASE_URL` points to the isolated database. |
| Implementation | [`test_persistence_config.py`](../../../tests/unit/test_persistence_config.py), [`test_postgres_persistence.py`](../../../tests/integration/test_postgres_persistence.py), [PR #31](https://github.com/swevazquez/SentinelOpsProject/pull/31) |
| Execution | `uv run pytest -q tests/unit/test_persistence_config.py`; then `SENTINELOPS_TEST_DATABASE_URL=postgresql://sentinelops:sentinelops@127.0.0.1:5432/sentinelops uv run pytest -q tests/integration/test_postgres_persistence.py` |
| Expected Result | Backend selection, schema bootstrap, restart retrieval, transaction rollback, and explicit unavailable behavior pass. |
| Result | Passed. Database-specific cases are environment-gated and skip only when the URL is absent. |
| Cleanup | Remove isolated test records or stop the database service. |

#### TC-INFRA-37 - Spark RUL Batch Boundary

| Field | Specification |
|---|---|
| Requirements | FR-03, FR-06, FR-08, FR-18, NFR-02 |
| Acceptance Criteria | Spark validates and types C-MAPSS-compatible input, invokes the shared versioned ML service, persists traceable predictions, and returns a nonzero/failure result for invalid input or artifacts. |
| Preconditions | Java 17+, Spark extra, prepared FD001 input, and model version `1.0.0`. |
| Implementation | [`test_spark_rul_batch.py`](../../../tests/unit/test_spark_rul_batch.py), [`test_spark_rul_batch.py`](../../../tests/integration/test_spark_rul_batch.py), [`test_spark_cli.py`](../../../tests/system/test_spark_cli.py), [PR #32](https://github.com/swevazquez/SentinelOpsProject/pull/32) |
| Execution | `uv run --extra spark pytest -q tests/unit/test_spark_rul_batch.py tests/integration/test_spark_rul_batch.py tests/system/test_spark_cli.py` |
| Expected Result | Valid batches produce traceable RUL results; missing columns, duplicate cycles, missing model artifacts, and invalid inputs fail before replacing committed results. |
| Result | Passed. |
| Cleanup | Test fixtures remove temporary input, output, and repository data. |

#### TC-INFRA-35 - Final Airflow Orchestration

| Field | Specification |
|---|---|
| Requirements | FR-04, FR-05, FR-11, FR-19, NFR-01, NFR-02 |
| Acceptance Criteria | The final manual-only DAG loads and executes `select_predictive_input`, `run_spark_rul_batch`, and `finalize_predictive_workflow` in order. Success advances the demo; failure releases the reserved checkpoint and records sanitized failed status. |
| Preconditions | Airflow test harness or Compose Airflow service, prepared RUL artifact, and shared data directory. |
| Implementation | [`test_airflow_pipeline.py`](../../../tests/unit/test_airflow_pipeline.py), [`test_airflow_pipeline.py`](../../../tests/integration/test_airflow_pipeline.py), [`test_airflow_client.py`](../../../tests/unit/test_airflow_client.py), [`test_airflow_api.py`](../../../tests/integration/test_airflow_api.py), [PR #33](https://github.com/swevazquez/SentinelOpsProject/pull/33) |
| Execution | `uv run pytest -q tests/unit/test_airflow_pipeline.py tests/integration/test_airflow_pipeline.py tests/unit/test_airflow_client.py tests/integration/test_airflow_api.py`; then run successive checkpoints through the dashboard. |
| Expected Result | DAG syntax, task order, trigger configuration, terminal state, next-checkpoint release, and failure callback pass. |
| Result | Passed. Chrome UAT confirmed the next checkpoint and Reset demo become available after terminal state without a refresh. |
| Cleanup | Reset the demo and stop Airflow after review. |

#### TC-INFRA-34 - Integrated Docker Compose Deployment

| Field | Specification |
|---|---|
| Requirements | FR-20, NFR-04, NFR-05 |
| Acceptance Criteria | Compose starts FastAPI, PostgreSQL, Airflow, and the Spark runtime with health checks; `/api/health` responds; a checkpoint completes through Airflow, Spark, and PostgreSQL; invalid configuration fails clearly. |
| Preconditions | Docker Desktop or Docker Engine is running and `.env` exists. |
| Implementation | [`test_api_health.py`](../../../tests/integration/test_api_health.py), [`test_compose_configuration.py`](../../../tests/system/test_compose_configuration.py), [`scripts/check-compose.sh`](../../../scripts/check-compose.sh), [PR #34](https://github.com/swevazquez/SentinelOpsProject/pull/34) |
| Execution | `bash scripts/check-compose.sh config`; `docker compose up -d --build --wait`; `curl --fail http://127.0.0.1:8000/api/health`; `docker compose ps`; open the dashboard and run one checkpoint. |
| Expected Result | Services become healthy, readiness responds, the integrated result appears in the UI, and shutdown with `docker compose down` preserves the named database volume. |
| Result | Passed. Focused Compose tests passed and live review produced the final UI evidence. |
| Cleanup | Run `docker compose down` after the demonstration. |

#### TC-SYS-CLEAN-01 - Clean Checkout

| Field | Specification |
|---|---|
| Requirements | NFR-04 |
| Acceptance Criteria | Prerequisites, setup, environment preservation, workflow execution, and generated-artifact safeguards succeed from an isolated copy. |
| Implementation | [`test_clean_checkout.py`](../../../tests/system/test_clean_checkout.py) |
| Execution | `uv run pytest -q tests/system/test_clean_checkout.py` |
| Expected Result | Setup is repeatable and required artifacts are generated without contaminating source control. |
| Result | Passed. |

#### TC-SYS-PERF-01 - Demonstration Performance

| Field | Specification |
|---|---|
| Requirements | NFR-08 |
| Acceptance Criteria | Three 24-hour, four-asset workflows each complete within five seconds and produce complete raw, feature, prediction, and status output. |
| Implementation | [`test_demo_performance.py`](../../../tests/system/test_demo_performance.py), [`demo_performance.py`](../../../scripts/demo_performance.py) |
| Execution | `./scripts/check-demo-performance.sh` |
| Expected Result | Every run passes threshold and completeness checks; a timing report is written. |
| Result | Passed; the recorded Sprint 2 run had a 0.0016-second maximum and 0.0013-second average. |

#### TC-SYS-REG-01 - Complete Validation

| Field | Specification |
|---|---|
| Requirements | FR-16, NFR-03, NFR-09, NFR-10 |
| Acceptance Criteria | All automated tests, smoke workflow, Airflow DAG syntax, Spark checks, Compose configuration checks, generated-data safeguards, and Markdown readability checks pass. |
| Implementation | [`check-ci.sh`](../../../scripts/check-ci.sh), [`test_component_boundaries.py`](../../../tests/architecture/test_component_boundaries.py) |
| Execution | `UV_CACHE_DIR=/tmp/sentinelops-uv-cache uv run --extra spark ./scripts/check-ci.sh` |
| Expected Result | The command exits zero and reports `CI checks passed.` |
| Result | Passed: 170 collected, 166 passed, and four environment-dependent cases skipped. |

### 3.3 User Acceptance Test Specifications

#### TC-UAT-DASH-01 - Operational Dashboard

| Field | Specification |
|---|---|
| Requirements | FR-10 |
| Acceptance Criteria | Overview, Assets, Workflows, and Assistant display live or clear empty/error state; controls remain readable at desktop and tablet widths. |
| Preconditions | Uvicorn running with sample asset data. |
| Procedure | Open the application at 1248x720 and 900x1000; review every view, details dialog, filter, navigation control, loading/empty states, and browser console. |
| Expected Result | Views are readable, navigation works, detail dialogs open/close, and no overlap, clipping, warning, or console error appears. |
| Evidence | [`test_dashboard_ui.py`](../../../tests/unit/test_dashboard_ui.py) and current browser review |
| Result | Passed. |

#### TC-UAT-WORKFLOW-01 - Manual Workflow

| Field | Specification |
|---|---|
| Requirements | FR-11 |
| Acceptance Criteria | A user can start the supported workflow, observe feedback and terminal status, and inspect its details. |
| Procedure | Open Workflows, select **Run workflow**, observe accepted feedback, refresh status, open the run, and inspect the timeline and traceable run identifier. |
| Expected Result | Exactly one workflow appears and reaches completed or failed with appropriate detail. |
| Result | Passed for the normal completion path. |

#### TC-UAT-RUL-01 - Repeatable RUL Demonstration

| Field | Specification |
|---|---|
| Requirements | FR-RUL-03 through FR-RUL-06 |
| Acceptance Criteria | Four workflow runs advance the configured engines through 40%, 60%, 80%, and 100% checkpoints; results show RUL separately from risk; summaries distinguish workflow success from findings; notifications accumulate until read or cleared; reset starts a repeatable active session. |
| Procedure | Run four workflows from Workflows; inspect summaries, asset details, model metadata, and notifications after each; open one notification; clear all; reset; run checkpoint one again. |
| Expected Result | The lifecycle sequence and active findings are understandable, historical results remain retrievable, and the reset session repeats the same checkpoint-one inputs and results. |
| Evidence | [`test_rul_experience.py`](../../../tests/e2e/test_rul_experience.py), [`test_dashboard_ui.py`](../../../tests/unit/test_dashboard_ui.py), and browser review |
| Result | Passed. |

#### TC-UAT-ASSIST-01 - Grounded Query

| Field | Specification |
|---|---|
| Requirements | FR-12, FR-13 |
| Acceptance Criteria | Supported asset, prediction, and workflow questions return grounded results and approved-tool evidence; unsupported scope is stated clearly. |
| Procedure | Submit highest-risk, asset explanation, workflow failure, and unsupported questions through Assistant. |
| Expected Result | Supported answers match current operational data; no unapproved tool executes. |
| Result | Passed with the controlled test client and browser UI behavior. The live provider is feature-dependent and outside automated acceptance. |

#### TC-UAT-APPROVAL-01 - Approval-Gated Action

| Field | Specification |
|---|---|
| Requirements | FR-14, NFR-06 |
| Acceptance Criteria | The action appears inline before execution; Reject starts no workflow; Approve and run starts one exact workflow; result details close back to Assistant and do not reopen on refresh. |
| Procedure | Request `Run predictive maintenance`; inspect impact, expiration, and fingerprint; reject and compare workflow count; repeat, approve, open the workflow link, close details, and refresh. |
| Expected Result | Rejection makes no operational change; approval creates one traceable run; navigation and refresh preserve the Assistant experience. |
| Result | Passed at desktop and tablet widths. |

## 4. Test Implementation and Execution

### 4.1 Source Organization

| Location | Content |
|---|---|
| `tests/unit/` | Focused module, UI-contract, policy, storage, and validation tests |
| `tests/integration/` | Cross-component API, Assistant, workflow, and scoring tests |
| `tests/system/` | Clean-checkout and performance tests |
| `tests/architecture/` | Component dependency rules |
| `tests/fixtures/` | Representative committed C-MAPSS data |
| `tests/fake_openai.py` | Deterministic Responses API substitute |
| `scripts/check-ci.sh` | Complete validation entry point |
| `.github/workflows/ci.yml` | GitHub Actions pipeline |

### 4.2 Execution Commands

```bash
uv sync --extra dev --extra spark
uv run pytest -q tests/unit
uv run pytest -q tests/integration
uv run pytest -q tests/system tests/architecture
uv run --extra spark ./scripts/check-ci.sh
./scripts/check-demo-performance.sh
```

UAT requires:

```bash
uv run uvicorn services.api.app:app --reload
```

Then open `http://127.0.0.1:8000`.

## 5. Final Test Results

### 5.1 Sprint 4 Integrated Baseline Results

The Sprint 4 integrated baseline reports:

| Test Level | Result | Scope |
|---|---|---|
| Unit | 127 tests collected | Data, workflow, API, ML training/inference, persistence configuration, Spark, RUL demo, agent, UI contracts, approval, audit, and C-MAPSS |
| Integration | 32 collected, 28 passed, 4 environment-gated skips | Workflow, RUL persistence/API, PostgreSQL, Spark, Airflow, Compose health, scoring, Assistant query/action, and approval execution |
| End-to-End | 1 test collected | End-to-end RUL experience and repeatable demonstration behavior |
| System and Architecture | 10 collected and passed | Clean checkout, Compose configuration, Spark CLI, repeated performance, and dependency boundaries |
| Full Regression | 170 collected, 166 passed, 4 skipped | Complete automated baseline plus smoke workflow, Airflow DAG syntax, Spark, Compose, generated-data, and Markdown readability checks |
| User Acceptance | Passed | Integrated Compose startup, four-checkpoint Airflow/Spark/PostgreSQL RUL lifecycle, asset results, summaries, notifications, reset, Assistant, approval, navigation, refresh, and responsive layout |

The only recurring warning is a Starlette TestClient deprecation notice concerning the current HTTPX integration. It does not fail tests but remains a dependency-maintenance item.

#### Environment-gated skipped tests

The four skipped cases are intentional integration tests that require the optional `SENTINELOPS_TEST_DATABASE_URL` environment variable. They are skipped when the local test command does not have a PostgreSQL service configured; they are not failures:

| Test | Reason for skip |
|---|---|
| `tests/integration/test_postgres_persistence.py::test_predictions_and_workflow_state_survive_api_recreation` (line 72) | `SENTINELOPS_TEST_DATABASE_URL` is required for PostgreSQL integration tests. |
| `tests/integration/test_postgres_persistence.py::test_prediction_repository_satisfies_query_contract` (line 140) | `SENTINELOPS_TEST_DATABASE_URL` is required for PostgreSQL integration tests. |
| `tests/integration/test_postgres_persistence.py::test_failed_replacement_keeps_last_committed_prediction_set` (line 169) | `SENTINELOPS_TEST_DATABASE_URL` is required for PostgreSQL integration tests. |
| `tests/integration/test_spark_rul_batch.py::test_spark_batch_persists_results_through_postgres_boundary` (line 184) | `SENTINELOPS_TEST_DATABASE_URL` is required for Spark/PostgreSQL testing. |

The Compose and user-acceptance evidence exercises the configured PostgreSQL path separately. The standard no-database regression command therefore reports these four cases as skipped rather than silently falling back to file storage.

### 5.2 Testing Progress

| Sprint Close | Automated Baseline | Major Test Growth | Quality Outcome |
|---|---:|---|---|
| Sprint 1 | 23 tests | Telemetry, features, workflow status, Airflow failure, clean checkout, architecture, and design review | Established repeatable data and workflow foundation |
| Sprint 2 | 67 tests | Scoring, indicators, storage, traceability, API, dashboard, and performance | Completed a demonstration-ready predictive slice |
| Sprint 3 | 117 tests | Manual workflows, Assistant tools/queries, C-MAPSS contract, action restriction, audit, approvals, and responsive UAT | Completed controlled interactive operations |
| Sprint 4 | 170 tests (4 skipped) | PostgreSQL persistence, Spark batch processing, final Airflow orchestration, Compose health, Random Forest training, RUL integration, repeatable demo, RUL API/UI/Assistant, notifications, and E2E validation | Integrated MVP path validated |

The automated baseline grew from 23 tests at Sprint 1 close to 170 tests in Sprint 4 while expanding from foundational processing to model training, RUL inference, PostgreSQL, Spark, Airflow, Compose, UI, security, AI-assisted behavior, and end-to-end acceptance.

## 6. Code Coverage Analysis

Coverage was measured with Python's standard-library `trace` module:

```bash
mkdir -p /tmp/sentinelops-final-trace
uv run --extra spark python -m trace --count --missing --summary \
  --coverdir /tmp/sentinelops-final-trace \
  --ignore-dir .venv \
  --module unittest discover -s tests
```

Final Sprint 4 measurement from the 170-test baseline:

| Scope / Module | Executable Lines | Covered | Missing | Coverage |
|---|---:|---:|---:|---:|
| Loaded Python application scope (`services/` and `airflow/`) | 4,599 | 3,837 | 762 | 83.4% |
| `services.ml.rul_training` | 489 | 389 | 100 | 79.6% |
| `services.ml.rul_inference` | 247 | 209 | 38 | 84.6% |
| `services.api.rul_demo` | 360 | 329 | 31 | 91.4% |
| `services.api.app` | 428 | 354 | 74 | 82.7% |
| `services.persistence.postgres` | 34 | 20 | 14 | 58.8% |
| `services.spark_jobs.rul_batch` | 241 | 225 | 16 | 93.4% |
| `services.workflows.airflow_pipeline` | 220 | 186 | 34 | 84.5% |

The tests execute important RUL paths, including training isolation, repeatability, artifact validation, maintenance mapping, atomic persistence, checkpoint progression, reset, API retrieval, grounded Assistant responses, dashboard contracts, and failure handling. Existing security tests also exercise allowlisting, closed schemas, approvals, replay prevention, and audit sanitization. The lower PostgreSQL repository percentage reflects paths that require a configured database and includes the four intentionally skipped integration cases described in Section 5.1.

The 83.4% result is statement execution reported by `trace` for Python modules under `services/` and `airflow/` that were loaded during this test run: 3,837 of 4,599 executable lines ran, while 762 did not. It is not branch coverage, and it does not measure static frontend JavaScript, Docker images, the PostgreSQL server, the Airflow scheduler, the Spark JVM, the external OpenAI service, or deployment environments not exercised by the command. Frontend behavior is represented through UI contract tests and manual UAT; service readiness and cross-container behavior are represented through integration and system tests. The result identifies useful automated-test depth and remaining gaps, but it is not a product-wide quality guarantee.

## 7. Defects, Failures, Warnings, and Limitations

| ID | Detection | Description | Severity | Disposition | Retest |
|---|---|---|---|---|---|
| DEF-01 | Architecture test | Performance validation initially crossed a forbidden workflow-package boundary. | Medium | Moved validation to `scripts/`. | Passed |
| DEF-02 | Self-review | Audit logging initially missed malformed model arguments rejected before tool dispatch. | High | Added pre-dispatch sanitized audit recording. | Passed |
| DEF-03 | Tablet UAT | Three-column action card overlapped in the narrow Assistant layout. | Medium | Updated responsive grid and full-width Assistant behavior. | Passed at 900x1000 |
| DEF-04 | User UAT | Approval in a separate popup interrupted the Assistant conversation. | Medium | Moved proposal and decisions into an inline card. | Passed |
| DEF-05 | User UAT | Closing workflow result details navigated to Workflows instead of preserving Assistant. | Medium | Preserved active Assistant view when details close. | Passed |
| DEF-06 | User UAT | Refreshing Assistant reopened stale workflow details. | Medium | Removed workflow-detail state from refresh/navigation state. | Passed |
| DEF-07 | RUL UAT | A green Completed label implied healthy assets even when the workflow found warning or critical conditions. | Medium | Separated successful pipeline execution from the asset-finding summary. | Passed |
| DEF-08 | RUL UAT | Demonstration reset left active assets and execution runs visible. | Medium | Reset now clears active assets, runs, counters, and notifications while retaining direct historical evidence. | Passed |
| DEF-09 | RUL UAT | New critical notifications replaced earlier warning notifications. | Medium | Findings now accumulate across the active session and clear individually when opened. | Passed |
| DEF-10 | RUL UAT | The notification inbox lacked a way to acknowledge every current finding. | Low | Added **Clear all** with an empty-state disabled condition. | Passed |
| WARN-01 | Automated tests | Starlette TestClient emits an HTTPX integration deprecation warning. | Low | Open dependency-maintenance item; no behavior failure. | Pending |
| LIMIT-01 | Architecture review | File-backed repositories do not provide production-grade multi-process consistency. | Accepted MVP limitation | PostgreSQL is the integrated review backend; file mode remains for local tests and development. | Not applicable |
| LIMIT-02 | Coverage review | Python coverage excludes frontend JavaScript statement coverage. | Medium | Use contract/UAT evidence for the static dashboard; no browser statement runner is required by the MVP. | Accepted limitation |

Expected failure log messages produced by negative tests are not product defects when the test asserts the failure and the overall case passes.

## 8. Requirements Traceability Matrix

| Requirement | Acceptance Focus | Unit | System / Integration | UAT | Result |
|---|---|---|---|---|---|
| FR-01 | Generate valid representative telemetry | TC-UNIT-DATA-01 | TC-SYS-WORKFLOW-01 | - | Passed |
| FR-02 | Persist traceable raw telemetry | TC-UNIT-DATA-01 | TC-SYS-WORKFLOW-01 | - | Passed |
| FR-03 | Produce validated per-asset features | TC-UNIT-DATA-01 | TC-SYS-WORKFLOW-01 | - | Passed |
| FR-04 | Execute processing stages in order | Workflow unit cases | TC-SYS-WORKFLOW-01 | TC-UAT-WORKFLOW-01 | Passed |
| FR-05 | Report running/completed/failed state | TC-UNIT-OPS-01 | TC-SYS-WORKFLOW-01 | TC-UAT-WORKFLOW-01 | Passed |
| FR-06 | Score every eligible asset | TC-UNIT-PRED-01, TC-UNIT-RUL-01 | TC-SYS-WORKFLOW-01, TC-INFRA-37 | TC-UAT-RUL-01 | Passed for RUL default and explicit baseline |
| FR-07 | Return risk, status, priority, recommendation | TC-UNIT-PRED-01 | TC-SYS-WORKFLOW-01 | TC-UAT-DASH-01 | Passed |
| FR-08 | Store and retrieve traceable predictions | TC-UNIT-PRED-01 | TC-SYS-WORKFLOW-01 | TC-UAT-DASH-01 | Passed |
| FR-09 | Expose operational API behavior | TC-UNIT-OPS-01 | API integration cases | Dashboard/Assistant evidence | Passed |
| FR-10 | Present responsive operational dashboard | UI contract unit cases | TC-SYS-REG-01 | TC-UAT-DASH-01 | Passed |
| FR-11 | Start supported workflow manually | API validation unit cases | TC-SYS-WORKFLOW-01 | TC-UAT-WORKFLOW-01 | Passed |
| FR-12 | Answer supported grounded questions | TC-UNIT-AGENT-01 | Assistant query integration | TC-UAT-ASSIST-01 | Passed |
| FR-13 | Restrict reads to approved tools | TC-UNIT-AGENT-01 | Assistant query integration | TC-UAT-ASSIST-01 | Passed |
| FR-14 | Require exact explicit approval | TC-UNIT-AGENT-01 | Assistant action integration | TC-UAT-APPROVAL-01 | Passed |
| FR-15 | Record meaningful safe events | TC-UNIT-OPS-01, TC-UNIT-AGENT-01 | Negative workflow/action cases | Reviewable audit evidence | Passed |
| FR-16 | Provide repeatable automated validation | All unit groups | TC-SYS-REG-01 | Reviewer execution | Passed |
| FR-17 | Persist predictions and workflow state in PostgreSQL | Persistence unit tests | TC-INFRA-36, TC-INFRA-34 | TC-UAT-RUL-01 | Passed |
| FR-18 | Provide the Spark RUL batch boundary | Spark unit tests | TC-INFRA-37, TC-INFRA-35 | TC-UAT-RUL-01 | Passed |
| FR-19 | Coordinate the final manual-only Airflow DAG | Airflow unit tests | TC-INFRA-35, TC-INFRA-34 | TC-UAT-WORKFLOW-01, TC-UAT-RUL-01 | Passed |
| FR-20 | Provide the integrated Compose deployment and readiness checks | Compose configuration tests | TC-INFRA-34, TC-SYS-REG-01 | TC-UAT-DASH-01, TC-UAT-RUL-01 | Passed |
| NFR-01 | Detect and report workflow failure | TC-UNIT-OPS-01 | Failure integration cases | Workflow failure detail | Passed |
| NFR-02 | Trace prediction to run and input | TC-UNIT-PRED-01 | TC-SYS-WORKFLOW-01 | Asset/workflow detail | Passed |
| NFR-03 | Preserve component boundaries | - | Architecture tests | - | Passed |
| NFR-04 | Support clean local setup | - | TC-SYS-CLEAN-01 | Reviewer setup | Passed |
| NFR-05 | Return clear API states | TC-UNIT-OPS-01 | API integration cases | UI error states | Passed |
| NFR-06 | Restrict AI-assisted writes | TC-UNIT-AGENT-01 | Action integration cases | TC-UAT-APPROVAL-01 | Passed |
| NFR-07 | Audit agent operations safely | TC-UNIT-AGENT-01 | Query/action integration | Audit review | Passed |
| NFR-08 | Complete demo workflow under threshold | - | TC-SYS-PERF-01 | Demo observation | Passed |
| NFR-09 | Execute major tests locally | All automated groups | TC-SYS-REG-01 | Reviewer execution | Passed |
| NFR-10 | Maintain readable documentation | - | Markdown validation | Reviewer document review | Passed |
| SAC data contract | Validate, label, and split FD001 | TC-UNIT-SAC-01 | Full regression | Document review | Passed |
| FR-RUL-01 | Prepare reproducible FD001 data | TC-UNIT-SAC-01 | TC-SYS-REG-01 | Document review | Passed |
| FR-RUL-02 | Train and evaluate Random Forest | TC-UNIT-RUL-01 | TC-SYS-REG-01 | Model evidence review | Passed |
| FR-RUL-03 | Run traceable default RUL inference | TC-UNIT-RUL-01 | TC-SYS-WORKFLOW-01, TC-SYS-RUL-01 | TC-UAT-RUL-01 | Passed |
| FR-RUL-04 | Retrieve compatible RUL results | API operation tests | TC-SYS-RUL-01 | TC-UAT-RUL-01 | Passed |
| FR-RUL-05 | Compare and explain RUL in dashboard | UI contract tests | TC-SYS-RUL-01 | TC-UAT-RUL-01 | Passed |
| FR-RUL-06 | Explain RUL through grounded tools | TC-UNIT-AGENT-01 | TC-SYS-RUL-01 | TC-UAT-ASSIST-01 | Passed |

## 9. CI/CD and Integration Evidence

GitHub Actions runs on every push and pull request targeting `main`. The final pipeline:

1. checks out the repository;
2. configures Python 3.12;
3. installs FastAPI, Uvicorn, HTTPX, OpenAI, pytest, and supporting dependencies;
4. runs `scripts/check-ci.sh`;
5. checks Jira traceability for pull requests.

`check-ci.sh` verifies the scaffold, rejects tracked generated data, runs all discovered tests, executes the workflow smoke test, validates raw/feature counts, compiles the Airflow DAG, and confirms Markdown files are readable.

The infrastructure pull requests passed CI before merge: [PR #31](https://github.com/swevazquez/SentinelOpsProject/pull/31), [PR #32](https://github.com/swevazquez/SentinelOpsProject/pull/32), [PR #33](https://github.com/swevazquez/SentinelOpsProject/pull/33), and [PR #34](https://github.com/swevazquez/SentinelOpsProject/pull/34). The final Compose validation run is recorded in [GitHub Actions job 91780011810](https://github.com/swevazquez/SentinelOpsProject/actions/runs/30841687751/job/91780011810). The local full regression collected 170 tests, passed 166, and skipped four environment-gated cases. Expected negative-path log messages in the output are asserted failure cases, not unexplained pipeline failures.

## 10. Overall Quality Assessment

The Sprint 4 baseline demonstrates strong automated and user-visible quality for the implemented scope. The full suite collected 170 tests, passed 166, and skipped four environment-gated cases; the measured loaded Python application scope has 83.4% statement execution; and UAT drove correction of meaningful RUL demonstration, notification, responsive, conversational, navigation, refresh, and integrated-stack issues. Remaining limitations are the 762 unexecuted Python lines, optional live OpenAI dependency, absent frontend statement coverage, the TestClient warning, and file-backed storage retained for focused local mode.
