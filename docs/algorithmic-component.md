# SentinelOps Significant Algorithmic Component Proposal

**Course:** SWENG 894 - Software Engineering Capstone Experience | **Project:** SentinelOps | **Student:** Eli Vazquez | **Date:** 2026-07-11 | **Repository:** <https://github.com/swevazquez/SentinelOpsProject>

**Related artifacts:** [Architecture documentation](README.md), [algorithm flow source](diagrams/algorithmic-component-flow.dot)

## 1. Product Overview

SentinelOps is a predictive-maintenance platform for reliability engineers, maintenance managers, and operations analysts. It addresses the operational problem of identifying degradation early enough to plan maintenance before an asset failure disrupts operations. The MVP generates telemetry, engineers features, scores asset risk, stores results, exposes operational APIs, and presents asset health and workflow status in a dashboard.

The proposed significant algorithmic component is a remaining useful life (RUL) model. Rather than only classifying assets with a rule-based risk score, SentinelOps will estimate the number of operating cycles an asset is expected to continue before failure. This learned maintenance horizon adds a data-driven planning capability that can be evaluated with model metrics, traced to its inputs, and displayed through the existing API and dashboard.

## 2. Algorithmic Solution Specification

The solution uses NASA's public C-MAPSS FD001 turbofan degradation dataset, which provides run-to-failure engine histories suitable for a feasible solo-capstone implementation. The target is the number of cycles remaining after each observed engine trajectory. NASA dataset reference: <https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data>.

The model is a seeded Random Forest regressor. It captures nonlinear sensor relationships, tolerates noisy features, and provides inspectable feature importance without requiring a complex deep-learning platform.

![Proposed training and runtime flow.](images/algorithmic-component-flow.svg)

The diagram separates offline model development from runtime scoring: historical run-to-failure data produces a versioned model, while current asset telemetry uses the matching feature pipeline to generate traceable API and dashboard outputs.

### Processing and Runtime Behavior

| Step | Behavior |
|---|---|
| 1 | Parse engine, cycle, operating-setting, and sensor fields; reject malformed records. |
| 2 | Label each row with `RUL = final cycle - current cycle` and cap early-life labels. |
| 3 | Remove constant sensors and create rolling-window statistics and trends. Fit preprocessing only on training engines to prevent leakage. |
| 4 | Split by engine identifier, never by row, so an engine cannot appear in both training and validation. |
| 5 | Train the seeded Random Forest and evaluate engine-level predictions with MAE and RMSE against a median-RUL baseline and the current risk baseline. |
| 6 | Persist the model, preprocessing metadata, selected features, dataset identifier, seed, metrics, and semantic model version. |
| 7 | Apply the same feature contract at runtime, predict RUL, derive bounded risk and maintenance bands, and store workflow/model traceability before API exposure. |

## 3. Rationale and Implementation Strategy

| What | How | Why |
|---|---|---|
| Add a learned maintenance horizon. | Train on FD001 and map RUL back to SentinelOps risk and priority terms. | RUL supports maintenance planning and demonstrates substantial algorithmic behavior beyond static pages or thresholds. |
| Keep the work maintainable. | Put training/evaluation in `services/ml`, feature preparation in Spark, coordination in Airflow, and results behind FastAPI and the dashboard. | Existing boundaries remain modular and understandable for a solo capstone. |
| Make results defensible. | Retain dataset, model, preprocessing, feature, seed, and metric metadata. | Reviewers can reproduce the input, evaluate performance, and trace each result. |

### Planned Implementation Sequence

1. **Dataset and contract:** acquire FD001, validate it, and document the preprocessing contract.
2. **Features and training:** construct engine-level RUL features, train/evaluate the model, and store metadata.
3. **Runtime integration:** connect inference to scoring, persistence, APIs, dashboard views, and end-to-end tests.

### Feasibility and Limitations

FD001 is a controlled benchmark rather than a complete representation of SentinelOps operations. The implementation will therefore treat the model as an evaluated capstone component, validate the feature contract between FD001 and SentinelOps telemetry, compare results with the existing rule-based baseline, and document domain-shift limitations rather than presenting the output as production-ready certainty.

### Acceptance Criteria

- A fixed seed produces repeatable outputs for identical training data.
- Training and validation are split by engine identifier.
- MAE and RMSE are documented against a naive baseline.
- Dataset, model input, and output metadata are retained for traceability.
- Missing model artifacts or required features fail clearly without breaking the current product flow.

## 4. Proposal Summary

This component expands SentinelOps from a rule-based MVP into a system that learns a maintenance horizon from degradation data. A Random Forest RUL model is significant enough to satisfy the capstone algorithmic requirement, feasible within the remaining schedule, and compatible with the current architecture and UI. Implementation stories will be refined after instructor feedback.
