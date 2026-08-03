# Docker Compose Deployment

This is the supported containerized path for reviewing the integrated SentinelOps MVP. It starts the FastAPI dashboard/API, PostgreSQL persistence, Airflow orchestration, and the Spark runtime used by the final RUL workflow.

## Prerequisites and configuration

Install Docker Desktop with Docker Compose support. From the repository root, run:

```bash
./scripts/setup.sh
```

The setup script creates `.env` from `.env.example` when it is missing and preserves an existing `.env`. The local `.env` is ignored by Git. Add `OPENAI_API_KEY` only when the optional Operations Assistant is being reviewed; the predictive-maintenance workflow does not require OpenAI.

## Start and verify

These commands are intended to be reproducible as the SCRUM-34 clean-checkout validation after `./scripts/setup.sh` creates the local `.env`.

Validate the resolved configuration before starting the stack:

```bash
bash scripts/check-compose.sh config
```

Start the services and wait for their health checks:

```bash
docker compose up --build --wait
```

The same live validation, including the API readiness request, is available through:

```bash
bash scripts/check-compose.sh live
```

Expected readiness evidence:

```bash
curl --fail http://127.0.0.1:8000/api/health
docker compose ps
```

The API readiness response is a non-secret health result. PostgreSQL must be healthy before Airflow initializes, and the API waits for both PostgreSQL and Airflow before starting. Open the dashboard at `http://127.0.0.1:8000/`; Airflow is available at `http://127.0.0.1:8080/`.

## Review the application

For the professor-facing RUL demonstration, prepare the local FD001 data and versioned model before running the workflow:

```bash
uv run python -m services.ml.cmapss acquire
uv run python -m services.ml.cmapss prepare
uv run python -m services.ml.rul_training
```

In the dashboard, open **Workflows** and run the four checkpoints in order. The API submits each run to Airflow; Airflow selects the held-out C-MAPSS trajectory, Spark performs batch RUL inference, and PostgreSQL stores the result and workflow state.

## Configuration failure and shutdown

Starting without `.env` fails clearly; run `./scripts/setup.sh` to create the local configuration. Do not commit `.env` or generated runtime data. The Compose defaults are intended for local academic review and do not replace production secret management.

Stop the stack while preserving the named PostgreSQL volume:

```bash
docker compose down
```

Do not run `docker compose down --volumes` unless the local PostgreSQL data should be permanently removed. Restarting with `docker compose up --build --wait` preserves the documented persistent database state.
