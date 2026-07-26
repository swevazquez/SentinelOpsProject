# Remaining Useful Life Requirements

## Mission and Scope

SentinelOps helps maintenance managers identify degrading assets early enough to
plan maintenance before failure. The implemented remaining-useful-life (RUL)
capability estimates a maintenance horizon from NASA C-MAPSS FD001 engine
trajectories, stores the result with model and workflow traceability, and exposes
that result through the API, dashboard, and operational assistant.

This specification covers only behavior implemented by SCRUM-30 through
SCRUM-33. It does not claim that FD001 estimates are production forecasts for
physical SentinelOps assets, and it does not include planned Spark,
PostgreSQL, or Airflow integration.

## System Context and Users

The maintenance manager compares stored asset results and prioritizes the
shortest maintenance horizons. A reviewer can reproduce model training and RUL
inference, inspect the supporting metadata, retrieve results through FastAPI,
and verify the dashboard or assistant presentation. The assistant has read-only
access to approved RUL lookup tools and cannot calculate or invent an estimate.

## Functional Requirements

### FR-RUL-01: Prepare reproducible model data

**User story:** SCRUM-30

**Requirement:** The system shall validate C-MAPSS FD001 source files, calculate
capped RUL labels, and partition engines so no engine is shared between training
and validation data.

**Acceptance criteria:**

- Required files, schema, numeric fields, engine cycles, and checksums are
  validated.
- RUL is calculated as the final engine cycle minus the current cycle and capped
  at 125 cycles.
- The same seed and source data reproduce the same engine-level partitions.

### FR-RUL-02: Train and evaluate the approved model

**User story:** SCRUM-31

**Requirement:** The system shall train a seeded Random Forest regressor using
training-only sensor selection and causal temporal features, then evaluate it
against a median-training-RUL baseline.

**Acceptance criteria:**

- Validation engines do not influence feature selection or fitted model state.
- MAE and RMSE are recorded overall and by validation engine.
- Model, feature contract, selected sensors, feature importance, seed, metrics,
  library version, and checksums are saved in a versioned artifact.

### FR-RUL-03: Run traceable RUL inference

**User story:** SCRUM-32

**Requirement:** The default predictive workflow shall validate a requested model
artifact, reuse its serialized feature contract, score the latest cycle for each
configured demonstration engine, and persist the results atomically.

**Acceptance criteria:**

- Each stored result contains RUL, bounded risk and health, maintenance status,
  priority, recommendation, workflow run, model, dataset, input, and timestamp
  traceability.
- Missing, corrupt, or incompatible inputs fail the workflow without replacing
  existing prediction results.
- RUL is the default workflow mode; the deterministic rule-based mode remains
  available only through an explicit development or test request.
- Each demonstration run stores the exact label-free trajectory used for
  inference and advances one of four configured lifecycle checkpoints.
- Completing all four checkpoints blocks another run until reset, while reset
  starts a new session without deleting prior inputs, workflow records, or
  predictions.

### FR-RUL-04: Retrieve compatible RUL results

**User story:** SCRUM-33

**Requirement:** The API shall provide the latest RUL results and RUL history for
a specified asset without substituting deterministic risk predictions.

**Acceptance criteria:**

- `GET /api/predictions/rul/latest` returns only stored RUL predictions.
- `GET /api/predictions/rul/assets/{asset_id}` returns only that asset's stored
  RUL history.
- A missing compatible result returns a clear unavailable response.

### FR-RUL-05: Compare and explain RUL in the dashboard

**User story:** SCRUM-33

**Requirement:** The dashboard shall let a maintenance manager compare assets by
maintenance horizon and inspect the information needed to interpret an RUL
result.

**Acceptance criteria:**

- Asset rows show RUL separately from risk and can be sorted by shortest RUL.
- Asset details show RUL cycles, health, priority, recommendation, model
  version, prediction time, and dataset.
- Assets without a stored RUL display `Unavailable`; their risk score is not
  presented as an RUL estimate.

### FR-RUL-06: Explain RUL through grounded assistant tools

**User story:** SCRUM-33

**Requirement:** The assistant shall answer supported RUL questions with stored
results obtained through approved read-only tools.

**Acceptance criteria:**

- The response exposes visible evidence for the RUL lookup tool used.
- Result items include the stored RUL cycles, health, priority,
  recommendation, model version, and timestamp.
- If no compatible RUL exists, the assistant states that RUL is unavailable and
  does not fabricate or derive a substitute estimate.

## Non-Functional Requirements

### NFR-RUL-01: Reproducibility

The same approved inputs, seed, feature contract, and model version shall produce
repeatable outputs. This supports academic review and makes model changes
auditable.

### NFR-RUL-02: Traceability

Every RUL result shall identify its workflow run, model version and checksum,
dataset and feature-contract versions, input fingerprint, and prediction
timestamp. This lets a reviewer connect an operational result to the artifact
that produced it.

### NFR-RUL-03: Safety and integrity

The system shall validate artifacts and data before persistence, write prediction
sets atomically, and prevent the assistant from replacing missing RUL with a
generated value. These controls reduce misleading maintenance guidance.

### NFR-RUL-04: Usability

The dashboard shall label RUL in cycles, keep RUL separate from risk, support
shortest-horizon sorting, and show an explicit unavailable state. This helps a
maintenance manager prioritize work without treating different indicators as
equivalent.

## Algorithmic Component Specification

The approved significant algorithmic component is a seeded Random Forest
regressor trained on C-MAPSS FD001 run-to-failure data. Training constructs
causal rolling statistics and trends from sensors selected using training data
only. Validation is isolated by engine identifier. The saved artifact contains
the fitted model and the exact temporal feature contract used at runtime.

At runtime, SentinelOps validates the artifact and trajectory schema, recreates
the saved features, predicts every row, and retains the latest-cycle estimate for
each engine. RUL is bounded to the supported 125-cycle horizon. Health is
`bounded RUL / 125`, and risk is `1 - health`. Existing risk thresholds convert
that bounded risk to status, maintenance priority, and a recommendation.

The model supports the system scope by adding a comparable planning horizon. It
does not predict a guaranteed failure date. FD001 is a simulated turbofan
benchmark, so the result demonstrates the implemented pipeline and contract
rather than establishing production validity for other asset types.

## Traceability

| Requirement | Story | Implementation | Verification |
|---|---|---|---|
| FR-RUL-01 | SCRUM-30 | `services/ml/cmapss.py` | `tests/unit/test_cmapss.py` |
| FR-RUL-02 | SCRUM-31 | `services/ml/rul_training.py` | `tests/unit/test_rul_training.py` |
| FR-RUL-03 | SCRUM-32 | `services/ml/rul_inference.py`, `services/api/workflow_runner.py` | `tests/unit/test_rul_inference.py`, `tests/integration/test_rul_workflow.py` |
| FR-RUL-04 | SCRUM-33 | `services/api/operations.py`, `services/api/app.py` | `tests/unit/test_api_operations.py`, `tests/e2e/test_rul_experience.py` |
| FR-RUL-05 | SCRUM-33 | `frontend/dashboard/index.html`, `frontend/dashboard/app.js` | `tests/unit/test_dashboard_ui.py`, `tests/e2e/test_rul_experience.py` |
| FR-RUL-06 | SCRUM-33 | `services/agent/tools.py`, `services/agent/assistant.py` | `tests/unit/test_agent_tools.py`, `tests/unit/test_agent_assistant.py`, `tests/e2e/test_rul_experience.py` |
