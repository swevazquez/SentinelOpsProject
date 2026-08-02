# Component Responsibilities

SentinelOps separates operational interfaces, orchestration, data processing,
analytics, simulation, and user interaction so each component has one primary
reason to change.

## Ownership Boundaries

| Component | Repository Location | Owns | Does Not Own |
|---|---|---|---|
| API | `services/api/` | FastAPI routes, request and response schemas, operational queries, and coordination of application services. | Workflow scheduling, feature engineering, model implementation, dashboard rendering, or agent policy. |
| Orchestration | `airflow/` and `services/workflows/` | Airflow scheduling, task dependency order, reusable workflow coordination, run status, and failure reporting. | Telemetry algorithms, feature calculations, model training, HTTP presentation, or user-interface rendering. |
| Processing | `services/spark_jobs/` and `services/spark-jobs/` | Spark batch input validation, typing, ordering, stable RUL batch invocation, and the original lightweight feature workflow. | Workflow scheduling, model rules, API routing, dashboard behavior, or agent decisions. |
| Analytics | `services/ml/` | Model training, evaluation, inference helpers, explainability, and model metadata. | Data ingestion, workflow scheduling, HTTP routing, dashboard rendering, or operational approvals. |
| Persistence | `services/persistence/`, repository adapters in `services/ml/` and `services/workflows/` | Backend selection, PostgreSQL connection handling, versioned schema bootstrap, and repository implementations for predictions and workflow state. | API response formatting, workflow scheduling, model inference, or dashboard behavior. |
| Simulator | `services/simulator/` | Deterministic representative telemetry generation and raw telemetry persistence. | Feature engineering, scheduling, analytics, APIs, dashboard behavior, or agent actions. |
| Dashboard | `frontend/dashboard/` | Operational views, client-side interaction, view state, and calls to documented API contracts. | Direct data-file access, workflow scheduling, model execution, or agent tool execution. |
| Agent | `services/agent/` | Natural-language operational assistance, narrow tool interfaces, audit context, and approval-gated actions. | Direct storage mutation, independent workflow scheduling, model training, or dashboard rendering. |

## Dependency Direction

Implemented Python dependencies follow this direction:

```text
Airflow DAG -> workflow coordination -> simulator and processing
Airflow DAG -> Spark RUL batch -> ML inference and persistence contracts
```

- Airflow DAGs delegate application behavior to `services.workflows`.
- Workflow coordination may compose simulator and processing capabilities.
- The simulator and original lightweight feature module remain independent of
  orchestration and interface components.
- The Spark RUL entrypoint may compose ML, prediction-repository, and shared
  workflow-status contracts, but it remains independent of Airflow and FastAPI.
- API, dashboard, analytics, and agent components will consume explicit
  application contracts as their later-sprint implementations are added.

Shared data is exchanged through explicit function arguments, return types, and
documented artifact contracts. Components must not reach into another component's
runtime state or bypass its public entrypoint.

Prediction and workflow consumers depend on repository protocols. Explicit
configuration selects file-backed adapters for lightweight local work or
PostgreSQL adapters for durable operational state. PostgreSQL failures surface as
unavailable states; they do not trigger an implicit switch to another backend.

## Automated Boundary Check

`tests/architecture/test_component_boundaries.py` parses Python imports and enforces
the current dependency direction. It protects the implemented components without
inventing constraints for modules that do not yet contain application code.

Run the focused check:

```bash
python3 -m unittest tests.architecture.test_component_boundaries -v
```

The complete `./scripts/check-ci.sh` command discovers this test automatically.
