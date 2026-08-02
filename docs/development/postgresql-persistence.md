# PostgreSQL Operational Persistence

SCRUM-36 adds durable PostgreSQL storage for prediction results and workflow
state. The application selects this implementation through configuration while
retaining file-backed CSV and JSON repositories for focused development and
tests.

## Configuration

| Setting | Value | Purpose |
|---|---|---|
| `SENTINELOPS_PERSISTENCE_BACKEND` | `file` | Default. Stores predictions under `data/predictions/` and workflow state under `data/workflow-status/`. |
| `SENTINELOPS_PERSISTENCE_BACKEND` | `postgres` | Uses the PostgreSQL implementations for predictions and workflow state. |
| `DATABASE_URL` | PostgreSQL connection URL | Required when the backend is `postgres`. |

From the repository root, start only PostgreSQL and then run the API against it:

```bash
docker compose up -d postgres
SENTINELOPS_PERSISTENCE_BACKEND=postgres \
DATABASE_URL=postgresql://sentinelops:sentinelops@127.0.0.1:5432/sentinelops \
  uv run uvicorn services.api.app:app --reload
```

The hostname is `127.0.0.1` when the API runs on the host. A later integrated
Compose story will configure the container-to-container hostname.

## Stored Records

Migration `services/persistence/migrations/001_operational_persistence.sql`
creates the following prefixed tables so they remain distinct from Airflow's
own metadata tables:

- `sentinelops_predictions` stores one JSON prediction payload per workflow run
  and asset, plus indexed run, asset, type, and scoring-time fields.
- `sentinelops_workflow_status` stores the latest state, step, error,
  approval identifier, and update time for each workflow run.
- `sentinelops_schema_migrations` records the applied operational schema version.

Prediction payloads preserve RUL, model version, model artifact fingerprint,
dataset identifier, feature-contract version, input fingerprint, asset or engine
identifier, workflow run identifier, and scoring timestamp. Repositories return
the same application-level dictionaries in either persistence mode.

## Consistency and Failure Behavior

- A complete prediction set is replaced within one database transaction.
- If replacement fails after it begins, PostgreSQL rolls back the transaction
  and retains the last committed prediction set.
- Workflow updates use an atomic upsert keyed by run identifier.
- An unavailable or misconfigured PostgreSQL backend produces an explicit
  unavailable response. SentinelOps does not silently report success or switch
  to file storage.
- File-backed prediction and workflow writes also use temporary-file replacement
  to avoid exposing partially written records.

## Verification

The normal test suite verifies the shared file-backed behavior, backend
selection, and unavailable-state handling. Run the PostgreSQL contract and API
recreation checks against the local service with:

```bash
SENTINELOPS_TEST_DATABASE_URL=postgresql://sentinelops:sentinelops@127.0.0.1:5432/sentinelops \
  uv run python -m unittest tests.integration.test_postgres_persistence
```

The integration tests verify that a new API instance retrieves the same
prediction and workflow records and that an interrupted replacement preserves
the last valid committed predictions.

## Backup and Reset Expectations

The RUL demo reset controls the active demonstration view; it does not delete
durable prediction or workflow history. Database backup and destructive reset
remain administrator operations.

Create a local SQL backup before resetting the database:

```bash
docker compose exec -T postgres \
  pg_dump -U sentinelops -d sentinelops > sentinelops-backup.sql
```

The named Compose volume retains database state when containers stop. Running
`docker compose down --volumes` permanently deletes that local PostgreSQL volume
and should be used only when an intentional full reset is required.

## Current Limitations

- Schema bootstrap supports the current single migration and is intentionally
  smaller than a general migration framework.
- Raw telemetry, processed features, model artifacts, demo scenario state,
  approvals, and audit logs remain file-backed in this story.
- Automated backup scheduling, retention policy, replication, and production
  credential management are outside the academic MVP scope.
