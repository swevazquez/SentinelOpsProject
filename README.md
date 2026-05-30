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

This repository has the Sprint 1 predictive-maintenance foundation in place:

1. Generate representative asset telemetry.
2. Persist raw telemetry under `data/raw/`.
3. Process telemetry into asset-level feature rows under `data/processed/`.
4. Orchestrate the telemetry and feature workflow with Airflow.
5. Validate core simulator and feature behavior with unit tests.

Prediction scoring, operational APIs, dashboard views, and AI-assisted interactions remain later-sprint work.

## Local Setup

Copy the environment template and run the setup script:

```bash
cp .env.example .env
./scripts/setup.sh
```

Run the local stack:

```bash
./scripts/run-local.sh
```

Seed sample data:

```bash
./scripts/seed-data.sh
```

Run the Sprint 1 unit tests:

```bash
python3 -m unittest discover -s tests
```

The Airflow DAG for Sprint 1 is `sentinelops_sprint1_pipeline`.

## Documentation

Project documentation is maintained under `docs/`:

- `docs/README.md`
- `docs/requirements/`
- `docs/architecture/`
- `docs/images/`
- `docs/diagrams/`

Documentation should be concise, traceable to project decisions, and appropriate for a graduate-level software engineering capstone.

## Jira and GitHub Traceability

Jira is the backlog source for user stories and sprint status. GitHub is the source of implementation evidence through branches, commits, pull requests, and CI checks.

Use Jira keys such as `SCRUM-4` in implementation branch names, pull request titles or bodies, and meaningful commits. See `docs/development/jira-github-traceability.md` for the project workflow and GitHub autolink setup.
