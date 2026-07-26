# SentinelOps

SentinelOps is a graduate-level Software Engineering capstone project focused on predictive maintenance, data engineering, workflow orchestration, and agentic AI integration.

The project demonstrates a realistic minimum viable product that connects telemetry simulation, batch data processing, machine learning, workflow orchestration, operational APIs, a web dashboard, and a controlled AI operations assistant.

## Project Goals

- Ingest and process simulated telemetry data.
- Engineer features for predictive maintenance use cases.
- Train and evaluate explainable machine learning models.
- Orchestrate workflows with Apache Airflow.
- Run batch data transformations with Apache Spark.
- Expose operational APIs through FastAPI.
- Display asset health, prediction, and pipeline status in a dashboard.
- Provide a single controlled AI assistant for operational queries and approved workflow actions.

## Architecture

SentinelOps uses a modular monorepo structure:

```text
services/api          FastAPI backend
services/agent        AI assistant and tool/function interfaces
services/ml           Model training, evaluation, and inference code
services/spark-jobs   PySpark ETL, feature, and scoring jobs
services/simulator    Telemetry data simulator
airflow               DAGs, plugins, and Airflow configuration
frontend/dashboard    Dashboard application
docs                  Capstone documentation
tests                 Unit, integration, and end-to-end tests
scripts               Local setup and developer utilities
data                  Local raw, processed, and sample data
```

## Development Status

This repository contains the completed Sprint 1 and Sprint 2 predictive-maintenance
foundation plus the first Sprint 3 interaction slices:

1. Generate representative asset telemetry.
2. Persist raw telemetry under `data/raw/`.
3. Process telemetry into asset-level feature rows under `data/processed/`.
4. Orchestrate the telemetry and feature workflow with Airflow.
5. Validate core simulator and feature behavior with unit tests.
6. Generate explainable asset risk scores from processed feature rows.
7. Classify asset status, maintenance priority, and recommended action.
8. Persist and retrieve prediction results through a repository interface.
9. Trace predictions to their workflow run and fingerprinted feature input.
10. Retrieve workflow execution status for completed, running, and failed runs.
11. Provide API routes for assets, workflows, latest predictions, and dashboard serving.
12. Display an API-integrated operations dashboard aligned with the reviewed UI wireframe.
13. Validate repeated demonstration-scale workflow performance.
14. Start the supported predictive-maintenance workflow through the dashboard and expose live status.
15. Provide controlled, read-only agent tools with closed schemas and API-bound execution.
16. Specify the significant Random Forest remaining-useful-life algorithm component using NASA C-MAPSS FD001.
17. Provide a modern operational dashboard with consistent cross-view interactions and a reusable design system.
18. Answer supported asset, prediction, and workflow questions through the OpenAI Responses API and approved tools.
19. Acquire and validate FD001 data, generate capped RUL labels, and create reproducible engine-level partitions.
20. Restrict AI-assisted writes to the predefined predictive-maintenance action.
21. Record sanitized, correlated audit evidence for every agent operation attempt.
22. Require exact, time-limited, single-use approval before an assistant action executes.
23. Train and evaluate a seeded Random Forest RUL model with engine-isolated FD001 data, temporal features, baseline metrics, and a versioned artifact.
24. Run versioned RUL inference through the predictive workflow with safe artifact validation, bounded maintenance indicators, persisted traceability, and API retrieval.
25. Compare and explain stored RUL results through dedicated APIs, the dashboard,
    and grounded read-only assistant tools with explicit unavailable states.

The Sprint 3 interaction slice now supports informational queries through
read-only tools and one approval-gated predictive-maintenance action. Unknown,
malformed, denied, expired, modified, and replayed action requests are rejected
before operational writes, and every attempt produces sanitized audit evidence.

## Local Setup

The local application requires Python 3.12 or later. The API and dashboard use
FastAPI and Uvicorn; development testing uses HTTPX and pytest. Docker Compose is
optional and is needed only to review the Airflow and PostgreSQL services.

Check local prerequisites:

```bash
./scripts/check-prerequisites.sh
```

Prepare the local environment:

```bash
./scripts/setup.sh
```

The setup command creates `.env` from `.env.example` when needed and creates local
runtime directories. It can be run repeatedly without overwriting an existing
`.env`.

Install the application and development dependencies:

```bash
uv sync --extra dev
```

Run the Sprint 1 workflow:

```bash
./scripts/seed-data.sh local-run
```

Expected artifacts:

```text
data/raw/telemetry_local-run.csv
data/processed/features_local-run.csv
data/workflow-status/workflow_local-run.json
```

Prepare FD001 and train the Random Forest RUL model:

```bash
uv run python -m services.ml.cmapss acquire
uv run python -m services.ml.cmapss prepare
uv run python -m services.ml.rul_training
```

The generated versioned model and its evaluation metadata are stored under
`data/models/rul-random-forest/`. NASA source data, processed partitions, and
model artifacts are local runtime evidence and are not committed.

Run the complete local validation suite:

```bash
uv run ./scripts/check-ci.sh
```

Run the focused Sprint 3 tests:

```bash
uv run pytest tests/integration/test_manual_workflow_api.py \
  tests/integration/test_assistant_query_api.py \
  tests/unit/test_api_operations.py \
  tests/unit/test_dashboard_ui.py \
  tests/unit/test_agent_tools.py \
  tests/unit/test_agent_assistant.py \
  tests/unit/test_cmapss.py \
  tests/unit/test_rul_training.py
```

Start the integrated API and dashboard:

```bash
uv run uvicorn services.api.app:app --reload
```

Open `http://127.0.0.1:8000` to review the dashboard. The Workflows view can
start the supported `predictive-maintenance` workflow and refresh live workflow,
asset, and prediction data.

After preparing FD001 and training model version `1.0.0`, the dashboard,
assistant action, and API run RUL inference by default:

```bash
curl -X POST http://127.0.0.1:8000/api/workflows \
  -H 'Content-Type: application/json' \
  -d '{"workflow":"predictive-maintenance"}'
```

The repeatable demonstration advances four held-out FD001 engines through 40%,
60%, 80%, and 100% of their recorded lifecycles. Every run stores a new
label-free trajectory, its source metadata, workflow status, and RUL results.
After checkpoint four, reset the scenario from the Workflows view or
`POST /api/workflows/rul-demo/reset`; prior evidence is retained.

Use the returned run ID with `GET /api/predictions/runs/{run_id}`, retrieve the
scenario with `GET /api/workflows/rul-demo/status`, or retrieve the current RUL
view with `GET /api/predictions/rul/latest`. The deterministic rule-based path
remains available for development and local testing by explicitly sending
`"inference_mode":"baseline"`.

Validate Sprint 2 demo performance:

```bash
./scripts/check-demo-performance.sh
```

The performance check runs three 24-hour demo workflows, stores predictions,
verifies raw, processed, prediction, and workflow-status outputs, and writes
ignored runtime evidence to `data/performance/latest-demo-performance.json`.

Start the optional Airflow and PostgreSQL services:

```bash
./scripts/run-local.sh
```

The Airflow DAG for Sprint 1 is `sentinelops_sprint1_pipeline`.

## Documentation

Project documentation is maintained under `docs/`:

- `docs/README.md`
- `docs/requirements/`
- `docs/architecture/`
- `docs/images/`
- `docs/diagrams/`
- `docs/algorithmic-component.md`
- `docs/reports/`

Documentation should be concise, traceable to project decisions, and appropriate for a graduate-level software engineering capstone.

## Jira and GitHub Traceability

Jira is the backlog source for user stories and sprint status. GitHub is the source of implementation evidence through branches, commits, pull requests, and CI checks.

Use Jira keys such as `SCRUM-4` in implementation branch names, pull request titles or bodies, and meaningful commits. See `docs/development/jira-github-traceability.md` for the project workflow and GitHub autolink setup.
