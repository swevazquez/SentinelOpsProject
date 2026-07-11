# SentinelOps Significant Algorithmic Component Proposal

# 1. Proposal Metadata

| Field | Value |
|---|---|
| Course | SWENG 894 - Software Engineering Capstone Experience |
| Project | SentinelOps |
| Student | Eli Vazquez |
| Document | Significant Algorithmic Component Proposal |
| Date | 2026-07-11 |
| Git Repository | <https://github.com/swevazquez/SentinelOpsProject> |
| Related Documentation | [docs/README.md](README.md), [docs/diagrams/algorithmic-component-flow.dot](diagrams/algorithmic-component-flow.dot) |

---

# 2. Product Overview

SentinelOps is a predictive-maintenance platform for reliability engineers, maintenance managers, and operations analysts. The current MVP already supports telemetry generation, feature processing, risk scoring, result storage, operational APIs, and a dashboard for reviewing asset health and workflow status.

The proposed significant algorithmic component is a remaining useful life (RUL) model. Instead of only classifying assets by a rule-based risk score, SentinelOps will estimate how many operational cycles an asset is expected to continue before failure. That estimate adds a data-driven maintenance horizon that can be shown through the existing API and dashboard layers.

This component shifts the project from static threshold scoring to a learned prognostics workflow. It gives the product a concrete algorithmic feature that can be validated with model metrics, traceability evidence, and visible downstream effects.

---

# 3. Algorithmic Solution Specification

The proposed solution uses NASA's public C-MAPSS FD001 turbofan degradation dataset. FD001 provides run-to-failure histories for a controlled set of engines, which makes it realistic enough to demonstrate advanced predictive logic while remaining feasible for a solo capstone project. NASA documents the task as estimating the cycles remaining after each test trajectory ends. <https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data>

The core model will be a Random Forest regressor. The model is well suited to this scope because it captures nonlinear relationships between sensors, tolerates noisy features, and provides feature importance that can be inspected during review.

![Proposed training and runtime flow.](images/algorithmic-component-flow.svg)

## Processing and Behavior

| Step | Behavior |
|---|---|
| 1 | Parse FD001 rows into engine, cycle, operating-setting, and sensor fields, then reject malformed or incomplete records. |
| 2 | Label each training row with `RUL = final engine cycle - current cycle`, then cap early-life RUL values so healthy observations do not dominate the model. |
| 3 | Remove constant sensors and build rolling-window statistics and trends for informative channels. Preprocessing is fit only on training engines to prevent leakage. |
| 4 | Split by engine identifier, not by row, so one engine cannot appear in both the training and validation sets. |
| 5 | Train a seeded Random Forest and evaluate engine-level predictions using mean absolute error (MAE) and root mean squared error (RMSE). Compare the model against a simple median-RUL baseline and the current SentinelOps risk baseline. |
| 6 | Persist the approved model, preprocessing metadata, selected features, training-data identifier, evaluation metrics, seed, and semantic model version. |
| 7 | At runtime, apply the same feature contract, predict RUL, derive a bounded risk and maintenance band, and store the result with workflow and model traceability before exposing it through current interfaces. |

---

# 4. Rationale and Implementation Strategy

| What | How | Why |
|---|---|---|
| Add a learned maintenance horizon instead of only rule-based scoring. | Train a Random Forest RUL model on FD001 and map the output back into SentinelOps risk and priority terms. | RUL is directly useful for maintenance planning and demonstrates a significant algorithmic component beyond static pages or threshold logic. |
| Keep the implementation maintainable for a solo capstone. | Place training and evaluation in `services/ml`, keep batch feature preparation in Spark, coordinate execution with Airflow, and expose results through FastAPI and the dashboard. | The architecture stays modular and understandable without introducing unnecessary complexity. |
| Make the proposal reviewable and defensible. | Track dataset version, model version, preprocessing metadata, selected features, and evaluation metrics. | Reviewers can verify the data source, the model choice, the performance, and the traceability of the result. |

## Planned Implementation Sequence

| Order | Story Focus | Deliverable |
|---|---|---|
| 1 | Dataset acquisition and validation | Reproducible access to FD001 and a documented preprocessing contract |
| 2 | Feature construction and training | Engine-level RUL features, model training, evaluation, and metadata storage |
| 3 | Runtime integration | Inference wiring into SentinelOps scoring, storage, API, dashboard, and end-to-end tests |

## Acceptance Criteria

- A fixed seed produces repeatable model outputs for the same training data.
- Training and validation data are split by engine identifier, not by row.
- MAE and RMSE are documented against a naive baseline.
- Model input, dataset version, and output metadata are retained.
- Missing model artifacts or required features do not break the current product flow.

---

# 5. Proposal Summary

This proposal expands SentinelOps from a rule-based predictive-maintenance MVP into a system that can learn a maintenance horizon from degradation data. The proposed RUL model is significant enough to satisfy the capstone algorithmic requirement, feasible within the remaining schedule, and compatible with the current architecture and UI.
