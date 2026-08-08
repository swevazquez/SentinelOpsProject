# SentinelOps Software End-User Manual

| Field | Value |
|---|---|
| Course | SWENG 894 - Software Engineering Capstone Experience |
| Product | SentinelOps |
| Author | Eli Vazquez |
| Document | Software End-User Manual |
| Version | 1.0 |
| Date | August 8, 2026 |
| Repository | [SentinelOpsProject](https://github.com/swevazquez/SentinelOpsProject) |

## 1. About This Manual

This manual serves two audiences:

1. **Maintenance managers and operational users** can use Part I to review equipment condition, identify assets that need attention, run an analysis, interpret maintenance indicators, and use the Assistant safely.
2. **Administrators and technical reviewers** can use Part II and the appendices to install, configure, deploy, verify, and troubleshoot SentinelOps.

No programming knowledge is required for the maintenance-manager procedures. Technical commands are separated from the day-to-day product instructions.

This manual describes the delivered SentinelOps application and its supported workflows.

## 2. Product Overview

SentinelOps is a predictive-maintenance application that helps maintenance managers identify equipment that may need attention. It brings current asset condition, maintenance priority, recommended action, workflow status, and supporting prediction evidence into one dashboard. The goal is to help a manager move from equipment data to a clear maintenance decision without manually reviewing raw telemetry.

The application also includes an Assistant that can answer supported questions about assets, predictions, and workflow history. The Assistant may propose starting the predictive-maintenance workflow, but it cannot start that operation until the user reviews and approves the exact action in the conversation.

Behind the dashboard, SentinelOps loads a versioned Random Forest model trained on NASA C-MAPSS FD001, prepares a label-free engine trajectory, estimates remaining useful life (RUL), derives maintenance indicators, records the result, and preserves workflow history. The repeatable demonstration advances four engines through 40%, 60%, 80%, and 100% lifecycle checkpoints. The deterministic risk path remains available only for explicit development and test use.

### 2.1 Main User Workflows

1. Review the operations overview.
2. Search and inspect asset health.
3. Run the predictive-maintenance workflow.
4. Review workflow history and execution details.
5. Review current risk, status, priority, and recommended action.
6. Compare RUL estimates and interpret the maintenance horizon.
7. Review and clear warning or critical notifications.
8. Ask the Assistant a supported operational question.
9. Review, reject, or approve an Assistant-proposed workflow action.

### 2.2 MVP Boundaries

SentinelOps is a local, single-user MVP. The recommended integrated deployment uses Docker Compose with FastAPI, PostgreSQL, Airflow, and a local Spark runtime. File-backed repositories remain available for focused development and tests. The application does not provide enterprise-scale concurrency, high availability, production authentication, or distributed deployment.

## Part I - Maintenance Manager Guide

## 3. Getting Started as a Maintenance Manager

Before using this part of the manual, an administrator must start SentinelOps and provide the application address. In the documented local environment, open:

```text
http://127.0.0.1:8000
```

The left navigation provides the primary work areas:

| Area | When to Use It |
|---|---|
| **Overview** | Begin here to understand current operating condition and recent activity |
| **Assets** | Find equipment, compare condition, and review a specific asset |
| **Workflows** | Start a new analysis or inspect current and previous runs |
| **Assistant** | Ask an operational question or review a proposed workflow action |

If the dashboard has no prediction data, run the predictive-maintenance workflow from **Workflows**. An empty state is not a system conclusion that every asset is healthy.

![SentinelOps Overview and navigation](../../images/reports/week-11-ui/overview.png)

*Figure SED-01. Overview page with navigation, fleet indicators, RUL distribution, and workflow evidence.*

## 4. Maintenance Manager Feature Catalog

The following table lists every user-facing workflow in this manual. Each feature has a matching procedure in Sections 5 and 6.

| Category | Feature | What It Helps the User Do | Related Requirement | Instructions |
|---|---|---|---|---|
| Monitoring | Operations overview | Review current asset condition and recent workflow activity | FR-10 | 5.1 |
| Asset review | Search and filter assets | Find equipment that may require attention | FR-10 | 5.2 |
| Asset review | Asset details and maintenance indicators | Review risk, status, priority, recommended action, and traceability | FR-06, FR-07, FR-08 | 5.3 |
| Asset review | RUL comparison and explanation | Compare maintenance horizons and inspect model, dataset, and prediction evidence | FR-RUL-04, FR-RUL-05 | 5.3 |
| Workflow | Run predictive maintenance | Generate a current set of asset predictions | FR-04, FR-11 | 5.4 |
| Workflow | Workflow history and details | Confirm that an analysis completed and investigate failures | FR-05, FR-10 | 5.5 |
| Workflow | Reset the active RUL demonstration | Clear the active session and repeat checkpoint one without deleting direct historical evidence | FR-RUL-03 | 5.6 |
| Monitoring | Operational notifications | Review accumulated warning and critical findings, acknowledge one, or clear all | FR-RUL-05 | 5.6 |
| Assistant | Ask an operational question | Retrieve supported asset, prediction, or workflow information in conversation | FR-12, FR-13 | 6.1 |
| Assistant | Reject a proposed action | Prevent an unwanted workflow from running | FR-14 | 6.2 |
| Assistant | Approve and review an action | Authorize one exact workflow and open its result without leaving the Assistant | FR-14 | 6.3 |

### 4.1 Supporting System Capabilities

The features above are supported by telemetry generation, feature processing, predictive scoring, workflow orchestration, persistence, API access, restricted actions, and sanitized audit logging. These capabilities operate behind the user interface. They are described in the deployment guide and technical appendices because a maintenance manager does not normally run them separately.

The RUL workflow and user experience use the recommended integrated path: FastAPI submits to Airflow, Airflow calls Spark, and PostgreSQL stores the results. Maintenance managers do not need to operate these services individually; the administrator starts them with Docker Compose.

| Supporting capability | What it does | Administrator entry point |
|---|---|---|
| PostgreSQL persistence | Stores predictions and workflow status durably across API restarts. | Compose PostgreSQL service; `docs/development/postgresql-persistence.md` |
| Spark batch processing | Validates C-MAPSS input and performs versioned RUL batch scoring. | Airflow task `run_spark_rul_batch` or the documented Spark CLI |
| Airflow orchestration | Selects a checkpoint, invokes Spark, and finalizes status. | DAG `sentinelops_predictive_maintenance` at `http://127.0.0.1:8080` |
| Docker Compose deployment | Starts and health-checks the integrated services. | `docker compose up --build --wait` and `/api/health` |

## 5. Dashboard Workflows

### 5.1 Review the Operations Overview

**Goal:** Understand the current operating condition and identify where further review is needed.

**Preconditions:** SentinelOps is running. At least one completed workflow is needed for current prediction results.

1. Open SentinelOps.
2. Select **Overview**.
3. Review the summary cards for the number and condition of monitored assets.
4. Review the prediction summary for assets with elevated maintenance status or priority.
5. Review the most recent workflow status to confirm that the displayed results came from a completed analysis.
6. Select an asset or workflow link when more detail is needed.

**Expected result:** The page displays current API-backed asset and workflow information. Assets requiring attention are distinguishable from assets in normal condition.

**If no data appears:** Open **Workflows**, run the predictive-maintenance workflow, and return after it completes.

**Maintenance decision:** Use the Overview to decide which assets need detailed review. Do not treat a failed or incomplete workflow as a valid all-clear result.

![Overview with current workflow results](../../images/reports/week-11-ui/overview.png)

*Figure SED-02. Overview with workflow results and assets requiring attention.*

### 5.2 Search and Filter Assets

**Goal:** Find a specific asset or narrow the list to equipment with a particular condition or priority.

**Preconditions:** At least one completed predictive-maintenance workflow.

1. Select **Assets**.
2. Review the asset list and its status and priority columns.
3. Enter an asset identifier in the search field when looking for specific equipment.
4. Apply an available status or priority filter to focus on assets that need attention.
5. Select an asset row to open its details.
6. Clear the search and filters to restore the complete list.

**Expected result:** The list updates without leaving the application. A selected asset opens with its latest available maintenance indicators.

**If no asset matches:** Clear the search and filters, confirm the asset identifier, and verify that the latest workflow completed.

![Asset health list](../../images/reports/week-11-ui/assets.png)

*Figure SED-03. Asset list sorted by remaining useful life, with risk, condition, priority, and recommended action.*

### 5.3 Interpret Asset Details and Maintenance Indicators

**Goal:** Understand why an asset has been prioritized and determine the next maintenance response.

1. Open an asset from **Assets** or from a link on **Overview**.
2. Confirm the asset identifier before acting on the result.
3. Review the latest workflow time so that the age of the prediction is understood.
4. Review **Remaining useful life** in operating cycles. A shorter horizon requires earlier review.
5. Review health and risk separately; RUL is not the same value as risk.
6. Review the maintenance priority and recommended action.
7. Confirm the model version, dataset, prediction time, workflow reference, and input traceability.

**How to interpret the result:**

- A higher risk or urgent priority indicates that the asset should be investigated sooner.
- The recommended action provides the application’s suggested next step; it does not replace organizational safety procedures or a qualified maintenance inspection.
- A result from an old, failed, or incomplete workflow should not be used as the current condition.
- RUL is an estimate from a model trained on simulated turbofan data. It is decision support, not a guaranteed failure date or a production-certified vehicle forecast.

**Expected result:** The user can identify the asset, the current maintenance concern, the suggested response, and the workflow that produced the result.

![Asset prediction details](../../images/reports/week-11-ui/asset-details.png)

*Figure SED-04. Asset details with RUL, risk, priority, recommendation, model metadata, dataset, and run traceability.*

### 5.4 Run the Predictive-Maintenance Workflow

**Goal:** Generate an updated set of maintenance results.

**Preconditions:** The application is running and no administrator has reported a service outage.

1. Select **Workflows**.
2. Select **Run checkpoint 1**. After each completed run, the button advances to the next available checkpoint.
3. Confirm that a new run appears with a running state.
4. Wait for the status to change to completed or failed.
5. Review the completion summary. Pipeline completion is shown separately from warning or critical asset findings.
6. Open the run to review the checkpoint, prediction count, shortest RUL, and asset results.
7. Return to **Overview** or **Assets** to compare the updated predictions.

**Expected result:** SentinelOps creates a unique run and advances four configured engines through one of four repeatable lifecycle checkpoints: 40%, 60%, 80%, or 100%. Each result contains RUL and supporting maintenance indicators.

**If the run fails:** Open the run, record its identifier and failure message, and contact the administrator. Do not interpret a failed run as a successful equipment assessment.

![Workflow execution and pipeline evidence](../../images/reports/week-11-ui/workflows.png)

*Figure SED-05. Workflow history, repeatable checkpoint controls, and Airflow-to-Spark pipeline timeline.*

### 5.5 Review Workflow History and Failures

**Goal:** Confirm when an analysis ran, whether it completed, and what happened during the run.

1. Select **Workflows**.
2. Search or filter the history when needed.
3. Select a run identifier.
4. Review its status, start and completion times, task sequence, and prediction count.
5. If the run failed, review the displayed failure information and record the run identifier for troubleshooting.
6. Use the back or close control to return to the workflow list.

**Expected result:** The detail view provides a clear execution timeline and distinguishes completed, running, and failed analyses.

### 5.6 Review and Clear Operational Notifications

**Goal:** Review warning and critical findings accumulated during the active demonstration session.

1. Run one or more predictive-maintenance workflows.
2. Select the notification bell.
3. Review the combined warning and critical findings from all active-session runs.
4. Select one notification to open the result that produced it. That notification becomes read.
5. Return to the bell and select **Clear all** when every current notification has been reviewed.

**Expected result:** New findings accumulate instead of replacing earlier findings. Opening one finding clears only that item. **Clear all** marks all current notifications as read and is disabled when none remain.

![Operational notification inbox](../../images/final-documentation/sed/notifications-clear-all.png)

*Figure SED-10. Notification inbox with accumulated findings, the unread count, and the Clear all control.*

To restart the active demonstration after the fourth checkpoint, use **Reset demo** in Workflows. Reset clears active assets, workflow history, counters, and notifications while retaining direct historical run evidence.

## 6. Assistant Workflows

Live Assistant questions require the administrator to configure the OpenAI service. The rest of SentinelOps remains usable if the Assistant is unavailable.

### 6.1 Ask a Supported Operational Question

**Goal:** Retrieve current operational information through a conversation.

1. Select **Assistant**.
2. Enter a question about assets, latest predictions, workflow history, or a specific workflow.
3. Submit the message.
4. Review the response and confirm that it refers to the expected asset or workflow.
5. Open a provided result link when more detail is needed.

![Operations Assistant](../../images/reports/week-11-ui/assistant.png)

*Figure SED-06. Operations Assistant with approved tools, system context, and grounded operational prompts.*

Example questions:

```text
Which assets need attention?
What is the latest prediction for FD001-ENGINE-002?
Show the most recent workflow status.
What happened in workflow <run-id>?
```

**Expected result:** The Assistant answers using the supported SentinelOps data sources.

**Alternative behavior:** An unsupported question receives a limitation response. If the Assistant service is unavailable, use the dashboard and notify the administrator.

The Assistant layout is shown in Figure SED-06. When a live provider is configured, the response and evidence card appear in the same conversation area.

### 6.2 Reject a Proposed Workflow Action

**Goal:** Decline a workflow proposal without starting a new analysis.

1. In **Assistant**, request that SentinelOps run the predictive-maintenance workflow.
2. Review the action proposal displayed inside the conversation.
3. Select **Reject**.
4. Confirm that the conversation records the rejection.
5. Open **Workflows** and verify that the rejected request did not create a run.

![Inline workflow approval proposal](../../images/final-documentation/sed/assistant-action-proposal.png)

*Figure SED-11. Inline protected-action proposal with its expiration, request fingerprint, Reject control, and Approve and run control.*

**Expected result:** The action does not execute.

The action proposal and rejected state remain inline in the Assistant conversation; no separate popup is used.

### 6.3 Approve and Review a Workflow Action

**Goal:** Authorize one exact workflow request and review its result without losing the Assistant conversation.

1. Request the predictive-maintenance workflow in **Assistant**.
2. Review the exact action displayed inside the conversation.
3. Select **Approve and run** only if the displayed action is correct.
4. Wait for the result to appear in the conversation.
5. Select the completed workflow link.
6. Review the workflow result.
7. Close the result.

**Expected result:** The approved action executes once. Closing the result returns to the Assistant, and refreshing the Assistant does not reopen an old workflow result.

![Completed Assistant workflow action](../../images/final-documentation/sed/assistant-action-completed.png)

*Figure SED-12. Completed approved action with the finding summary and a direct link to the workflow result.*

Create a new proposal instead of approving when the action is unexpected, has changed, or has expired. A used approval cannot be executed again.

The same inline card shows the exact action, approval expiration, and execution result.

## Part II - Administrator Installation and Deployment Guide

Part II provides the technical detail an administrator needs to install, configure, deploy, verify, and troubleshoot the application. Maintenance managers may skip Part II when SentinelOps has already been started for them.

## 7. Supported Environment

The verified reference environment is macOS with a terminal, Python 3.12 or later, Java 17 or later, Docker Compose, Git, and current Google Chrome. Linux is also supported by the command-line tooling. Windows users may use WSL 2, but those environments were not included in acceptance testing.

The recommended integrated launch uses Docker Compose. It starts the FastAPI dashboard/API, PostgreSQL operational persistence, Airflow orchestration, and the Spark runtime. A host-only Uvicorn launch with file-backed storage remains available for focused development and tests.

## 8. Tools, Frameworks, APIs, and Services

| Item | Purpose | Required? | Installation or Documentation |
|---|---|---:|---|
| Git | Clone and update the repository | Yes | [Git downloads](https://git-scm.com/downloads) |
| Python 3.12+ | Run the API, workflows, scripts, and tests | Yes | [Python downloads](https://www.python.org/downloads/) |
| `uv` | Manage Python dependencies and commands | Yes | [`uv` installation](https://docs.astral.sh/uv/getting-started/installation/) |
| Web browser | Use the dashboard and Assistant | Yes | [Google Chrome](https://www.google.com/chrome/), used during acceptance testing; other modern browsers were not included in that testing |
| FastAPI | Provide the REST API and serve the dashboard | Project dependency | [FastAPI documentation](https://fastapi.tiangolo.com/) |
| Uvicorn | Run the local ASGI application | Project dependency | [Uvicorn documentation](https://uvicorn.dev/) |
| OpenAI API | Enable live natural-language Assistant responses | Assistant only | [OpenAI API documentation](https://developers.openai.com/api/docs) |
| Docker Desktop or Docker Engine | Runs the integrated application stack | Required for the integrated deployment; optional for host-only development | [Get Docker](https://docs.docker.com/get-started/get-docker/) |
| Docker Compose | Starts and connects the API, PostgreSQL, Airflow, and Spark services | Required for the integrated demo | Included with Docker Desktop |
| Apache Airflow 2.10.5 | Manual-only orchestration of the integrated RUL workflow | Compose service | [Airflow 2.10.5 documentation](https://airflow.apache.org/docs/apache-airflow/2.10.5/) |
| PostgreSQL 16 | Durable prediction and workflow persistence | Compose service | [PostgreSQL documentation](https://www.postgresql.org/docs/) |
| Apache Spark and Java 17+ | C-MAPSS batch validation, feature preparation, and RUL scoring | Spark/Java are included in Compose; the current prerequisite script also validates host Java for the complete local toolchain | [Spark documentation](https://spark.apache.org/docs/latest/) |
| NASA C-MAPSS FD001 | Prepare RUL training and evaluation data | SAC feature only | [NASA C-MAPSS dataset](https://data.nasa.gov/dataset/groups/cmapss-jet-engine-simulated-data) |

FastAPI, Uvicorn, HTTPX, OpenAI, pytest, and other Python packages are installed from `pyproject.toml`; they do not need to be installed one at a time.

## 9. Download and Install the Required Tools

### 9.1 Install Git

Use the official installer for the operating system, then verify:

```bash
git --version
```

Expected result: the terminal prints an installed Git version.

### 9.2 Install Python

Install Python 3.12 or later, then verify:

```bash
python3 --version
```

Expected result: the reported version is 3.12 or newer.

### 9.3 Install `uv`

Follow the official `uv` installation instructions, then verify:

```bash
uv --version
```

Expected result: the terminal prints an installed `uv` version.

### 9.4 Install Docker for the Integrated Demo

Install Docker Desktop or Docker Engine for the integrated demo. Start Docker and verify:

```bash
docker compose version
```

Expected result: the Compose plugin version is displayed.

### 9.5 Install Java 17

The integrated Docker Compose images include their own Java/Spark runtime. The
current `check-prerequisites.sh` script also verifies Java 17 or later on the host
so that the complete local toolchain and host Spark path remain available.
Install host Java before running `setup.sh`.

Install a supported Java 17 distribution, then verify:

```bash
java -version
```

Expected result: the terminal reports Java 17 or later.

## 10. Download and Configure SentinelOps

Run all remaining commands from a terminal.

### 10.1 Clone the Repository

```bash
git clone https://github.com/swevazquez/SentinelOpsProject.git
cd SentinelOpsProject
```

Expected result: the terminal is in the repository root, which contains `pyproject.toml`, `services/`, `frontend/`, `tests/`, and `scripts/`.

### 10.2 Check Prerequisites

```bash
./scripts/check-prerequisites.sh
```

Expected result: Python 3.12 or later and Java 17 or later are accepted. For the integrated demo, confirm that the output reports a Docker Compose version. If it reports Docker Compose as unavailable, install or start Docker before continuing.

### 10.3 Prepare the Local Environment

```bash
./scripts/setup.sh
```

This creates `.env` from `.env.example` when `.env` does not exist and prepares the local runtime directories. Running it again does not overwrite an existing `.env`.

Expected result: `.env` and the required `data/` subdirectories exist.

The clean-checkout verification on August 8, 2026 completed the prerequisite
check, created `.env`, prepared the runtime directories, installed dependencies,
and validated the resolved Compose configuration without errors.

### 10.4 Review Environment Configuration

Open `.env` in a text editor. The important settings are:

| Variable | Purpose | Default or Guidance |
|---|---|---|
| `API_HOST` | API bind address | `0.0.0.0` |
| `API_PORT` | API port | `8000` |
| `SENTINELOPS_WORKFLOW_BACKEND` | Selects local or Airflow workflow execution | `local` for host development; Compose overrides to `airflow` |
| `SENTINELOPS_PERSISTENCE_BACKEND` | Selects file or PostgreSQL operational storage | `file` for host development; Compose overrides to `postgres` |
| `DATABASE_URL` | PostgreSQL connection URL | Compose uses `postgresql://sentinelops:sentinelops@postgres:5432/sentinelops` |
| `AIRFLOW_API_URL`, `AIRFLOW_API_USERNAME`, `AIRFLOW_API_PASSWORD` | API connection used by FastAPI to trigger Airflow | Defaults in `.env.example`; Compose uses the Airflow service hostname |
| `AIRFLOW_DAG_ID` | Predictive-maintenance DAG name | `sentinelops_predictive_maintenance` |
| `SENTINELOPS_AIRFLOW_MODEL_VERSION` | RUL artifact version used by the DAG | `1.0.0` |
| `SENTINELOPS_AIRFLOW_INPUT_PATH` | Optional explicit C-MAPSS input | Leave blank to use the next repeatable demo checkpoint |
| `SPARK_MASTER_URL` | Local Spark execution mode | `local[2]` |
| `OPENAI_API_KEY` | Enables live Assistant queries | Leave blank when Assistant access is not being tested |
| `OPENAI_MODEL` | Assistant model | Project default |
| `AGENT_REQUIRE_APPROVAL` | Preserves the approval gate | `true` |

Never place a real secret in documentation, screenshots, commits, or chat messages. A safe example is:

```text
OPENAI_API_KEY=your-key-here
```

If `OPENAI_API_KEY` is missing, the dashboard, workflows, APIs, and risk scoring remain usable. A live Assistant query returns an unavailable-service response instead of inventing an answer.

### 10.5 Install Project Dependencies

```bash
uv sync --extra dev --extra spark
```

Expected result: `uv` creates or updates the project environment and installs the application and development dependencies.

## 11. Validate and Start the Application

### 11.1 Run the Full Local Validation

```bash
UV_CACHE_DIR=/tmp/sentinelops-uv-cache uv run --extra spark ./scripts/check-ci.sh
```

Expected result: 170 tests are collected, 166 pass, four environment-dependent cases are skipped when their external service is not configured, and workflow smoke, Airflow syntax, Spark, generated-data, and Markdown checks pass.

### 11.2 Start FastAPI and the Dashboard

```bash
uv run uvicorn services.api.app:app --reload
```

Keep this terminal open. Expected result: Uvicorn reports that it is serving the application on port 8000.

Open:

```text
http://127.0.0.1:8000
```

Expected result: the SentinelOps Overview page loads.

### 11.3 Verify the API

Open a second terminal in the repository root:

```bash
curl --fail http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/assets
```

Expected result: `/api/health` returns a non-secret readiness response and `/api/assets` returns JSON containing an `assets` collection.

![Healthy API readiness response](../../images/final-documentation/sed/compose-api-health.png)

*Figure SED-07. Live `/api/health` response from the integrated Compose stack on August 8, 2026.*

### 11.4 Stop the Application

Return to the Uvicorn terminal and press `Control-C`.

Expected result: the server shuts down and port 8000 is released.

## 12. Prepare Demonstration Data

Two supported paths are available.

### 12.1 Generate Telemetry and Features from the Terminal

```bash
./scripts/seed-data.sh local-run
```

Expected artifacts:

```text
data/raw/telemetry_local-run.csv
data/processed/features_local-run.csv
data/workflow-status/workflow_local-run.json
```

This seed command demonstrates telemetry generation and feature processing. It does not create the complete prediction result. To generate predictions, run the complete predictive-maintenance workflow from the dashboard or the workflow API.

### 12.2 Run the Complete Workflow from the Dashboard

1. Start the application.
2. Open `http://127.0.0.1:8000`.
3. Select **Workflows**.
4. Select **Run workflow**.
5. Wait for the status to change from running to completed.

Expected result: a label-free RUL trajectory, predictions, model and input traceability, and workflow-status evidence are created for the new run.

## 13. Integrated Airflow, Spark, PostgreSQL, and Docker Compose Deployment

Docker must be running and `.env` must exist.

Before the first RUL demo, prepare the data and versioned model from the repository root:

```bash
uv run python -m services.ml.cmapss acquire
uv run python -m services.ml.cmapss prepare
uv run python -m services.ml.rul_training
```

The model artifact should include version `1.0.0` under `data/models/rul-random-forest/`. These generated data and model files remain local runtime evidence and are not committed to Git.

Validate the resolved configuration:

```bash
bash scripts/check-compose.sh config
```

Start the complete stack and wait for health checks:

```bash
docker compose up --build --wait
```

The equivalent live readiness check is:

```bash
bash scripts/check-compose.sh live
```

The dashboard is available at `http://127.0.0.1:8000`, PostgreSQL at the local
port 5432, and Airflow at:

```text
http://127.0.0.1:8080
```

Use the credentials configured in `.env` to sign in to Airflow. The development defaults are `airflow` / `sentinelops`; change them before any non-local deployment and do not publish credentials.

In Airflow, verify that `sentinelops_predictive_maintenance` is visible and manual-only. The task sequence is `select_predictive_input` → `run_spark_rul_batch` → `finalize_predictive_workflow`.

![Healthy Airflow services](../../images/final-documentation/sed/compose-airflow-health.png)

*Figure SED-08. Live Airflow health response showing healthy metadata database, scheduler, and triggerer after Compose startup on August 8, 2026.*

For normal integrated use, start workflows from the dashboard rather than triggering Airflow directly:

1. Open **Workflows**.
2. Select **Run checkpoint**.
3. Wait for the run to finish and confirm that the next checkpoint is enabled.
4. Review the result in **Overview**, **Assets**, or the run detail.
5. Repeat for checkpoints 2 through 4.
6. Use **Reset demo** when rehearsing the lifecycle again.

The API container uses PostgreSQL and Airflow service hostnames automatically. Airflow invokes the Spark RUL batch, and PostgreSQL stores predictions and workflow status. The model and demo input artifacts are shared through the mounted repository data directory.

To stop the integrated services:

```bash
docker compose down
```

Expected result: the Airflow and PostgreSQL containers stop. Local mounted data remains unless explicitly removed.

![Integrated workflow screen](../../images/reports/week-11-ui/workflows.png)

*Figure SED-09. The dashboard view used for the Airflow-to-Spark-to-PostgreSQL demonstration.*

## Appendix A - REST API Instructions

The API base URL is:

```text
http://127.0.0.1:8000
```

### A.1 List Assets

```bash
curl http://127.0.0.1:8000/api/assets
```

### A.2 Retrieve Latest Predictions

```bash
curl http://127.0.0.1:8000/api/predictions/latest
```

Retrieve only current RUL predictions:

```bash
curl http://127.0.0.1:8000/api/predictions/rul/latest
```

Retrieve RUL history for one asset:

```bash
curl http://127.0.0.1:8000/api/predictions/rul/assets/<asset-id>
```

### A.3 List Workflows

```bash
curl http://127.0.0.1:8000/api/workflows
```

### A.4 Retrieve One Workflow

Replace `<run-id>` with an existing identifier:

```bash
curl http://127.0.0.1:8000/api/workflows/<run-id>
```

### A.5 Start the Supported Workflow

```bash
curl -X POST http://127.0.0.1:8000/api/workflows \
  -H "Content-Type: application/json" \
  -d '{"workflow":"predictive-maintenance"}'
```

Expected result: the API returns an accepted workflow response with a run identifier. Unknown workflow names and malformed payloads are rejected.

### A.6 Review or Reset the RUL Demonstration

```bash
curl http://127.0.0.1:8000/api/workflows/rul-demo/status
curl -X POST http://127.0.0.1:8000/api/workflows/rul-demo/reset
```

Reset clears the active demonstration views and begins a new session. It does not delete prior trajectory, prediction, or workflow evidence available through direct run interfaces.

The Assistant also uses:

- `POST /api/assistant/query`
- `POST /api/assistant/approvals/{approval_id}`
- `POST /api/assistant/actions/execute`

These endpoints enforce the same tool, action, approval, and audit controls used by the dashboard.

## Appendix B - Data and Algorithm Instructions

### B.1 Review Generated Artifacts

After a completed workflow, inspect:

```text
data/raw/
data/processed/
data/predictions/
data/workflow-status/
data/audit/
```

Each prediction contains a workflow reference and input fingerprint so an administrator can connect the result to its source data.

### B.2 Prepare C-MAPSS FD001

The repository contains the implemented FD001 acquisition, validation, parsing, capped-label, engine-partition, training, evaluation, and inference contracts.

```bash
uv run python -m services.ml.cmapss acquire
uv run python -m services.ml.cmapss prepare
uv run python -m services.ml.rul_training
```

Verify:

1. the source archive or files match the expected dataset;
2. train and test rows parse using the expected schema;
3. RUL labels are capped according to the specification;
4. engines do not cross training, validation, and test partitions;
5. metadata records the source, processing configuration, selected features, metrics, seed, checksums, and semantic model version;
6. the artifact is stored under `data/models/rul-random-forest/` and is available to the default workflow.

After training, start the application and run the workflow from Workflows. Use `GET /api/predictions/rul/latest` to inspect current RUL results or `GET /api/workflows/rul-demo/status` to inspect the active checkpoint.

## Appendix C - Testing and Validation

### C.1 Full Regression

```bash
UV_CACHE_DIR=/tmp/sentinelops-uv-cache uv run --extra spark ./scripts/check-ci.sh
```

### C.2 Focused RUL Validation

```bash
uv run pytest \
  tests/integration/test_manual_workflow_api.py \
  tests/e2e/test_rul_experience.py \
  tests/unit/test_rul_training.py \
  tests/unit/test_rul_inference.py \
  tests/unit/test_rul_demo.py \
  tests/unit/test_agent_tools.py \
  tests/unit/test_agent_assistant.py \
  tests/unit/test_dashboard_ui.py \
  tests/unit/test_cmapss.py
```

### C.3 Demonstration Performance

```bash
./scripts/check-demo-performance.sh
```

Expected result: three demonstration-scale workflows finish within the configured threshold and write ignored evidence to `data/performance/latest-demo-performance.json`.

### C.4 Manual Acceptance Review

Complete the following at desktop and tablet widths using the Compose stack:

1. verify `/api/health` and open Overview;
2. search and select an asset;
3. Run and inspect a workflow;
4. ask a supported Assistant question;
5. reject one proposed action;
6. approve a new exact action;
7. open and close the workflow result;
8. refresh Assistant and verify no stale result overlay appears.

## Appendix D - Troubleshooting

| Symptom | Likely Cause | Resolution |
|---|---|---|
| Python prerequisite fails | Python is older than 3.12 | Install a supported Python version and rerun the check |
| `uv` is not found | `uv` is missing or not on `PATH` | Install `uv`, restart the terminal, and verify `uv --version` |
| Port 8000 is in use | Another local server is running | Stop the other process or launch Uvicorn on another port |
| Dashboard loads without data | No complete workflow has run | Run the workflow from Workflows or `POST /api/workflows` |
| Seed data has no predictions | `seed-data.sh` runs only telemetry and feature processing | Run the complete predictive-maintenance workflow |
| Assistant returns unavailable | `OPENAI_API_KEY` is missing or invalid | Configure a valid key and restart Uvicorn |
| Action does not execute | Request was rejected, expired, changed, malformed, or already used | Create a new request and approve the exact current proposal |
| Workflow result reappears after refresh | Stale browser assets or an old application revision | Hard refresh and confirm the current application release is running |
| Airflow does not start | Docker is stopped or resources/ports are unavailable | Start Docker, inspect `docker compose logs airflow`, and check ports 5432 and 8080 |
| Compose port 8000 does not show FastAPI | API readiness or a dependency health check has not completed | Run `docker compose ps`, inspect `docker compose logs api`, and retry `/api/health` after PostgreSQL and Airflow are healthy |
| PostgreSQL persistence is unavailable | Database service or connection settings are invalid | Check `docker compose ps postgres`, confirm `.env`, and review the explicit unavailable response; the Compose API does not silently fall back to files |
| Spark batch fails | Java/runtime, model artifact, or C-MAPSS input is missing | Run the FD001 preparation/training commands, inspect Airflow task logs, and verify `SENTINELOPS_AIRFLOW_MODEL_VERSION` |
| Tests show an HTTPX warning | Known TestClient deprecation warning | Record it as a non-failing warning and update dependencies when compatible |

## Appendix E - Visual Evidence Index

| Figures | Evidence Covered |
|---|---|
| SED-01 and SED-02 | Navigation, fleet overview, RUL distribution, alerts, and workflow context |
| SED-03 and SED-04 | Asset search, RUL ordering, maintenance indicators, model metadata, and run traceability |
| SED-05 | Repeatable checkpoint controls, workflow history, execution detail, and Airflow-to-Spark timeline |
| SED-06 | Assistant navigation, supported prompts, current system context, and approval-gated operating mode |
| SED-07 and SED-08 | Live API and Airflow readiness responses from the integrated Compose deployment |
| SED-09 | Dashboard entry point for the Airflow-to-Spark-to-PostgreSQL demonstration |
| SED-10 | Accumulated operational notifications, unread count, individual findings, and Clear all control |
| SED-11 | Inline exact-action review, expiration, request fingerprint, rejection, and approval controls |
| SED-12 | Completed approved action, finding summary, and direct workflow-result link |

All application images come from the delivered application. The readiness captures were
taken from the live integrated stack on August 8, 2026. They contain no API key,
private path, local username, or unrelated browser content.
