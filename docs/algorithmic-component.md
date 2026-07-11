---
title: "SentinelOps Significant Algorithmic Component"
author: "Eli Vazquez"
date: "2026-07-11"
format:
  pdf:
    pdf-engine: xelatex
    geometry:
      - margin=0.55in
    fontsize: 9.5pt
    linestretch: 0.95
    toc: false
    colorlinks: true
---

## Product Overview

SentinelOps is a predictive-maintenance platform for reliability engineers,
maintenance managers, and operations analysts. Its MVP coordinates telemetry
generation, feature processing, predictive scoring, result storage, APIs, and
an operational dashboard. The current scorer is a transparent rule-based
baseline: fixed weights convert temperature, vibration, pressure, runtime, and
observed failure signals into a risk score. This supports a demonstrable
workflow, but its weights are not learned from equipment degradation history.

The proposed significant algorithmic component will estimate **remaining useful
life (RUL)**: the number of operational cycles an asset is expected to continue
before failure. RUL adds a direct, data-derived maintenance-planning capability.
SentinelOps will translate the predicted cycles into its existing risk status,
maintenance priority, and recommended action so the result remains useful in
the API and dashboard.

## Algorithmic Solution Specification

The model will use NASA's public **C-MAPSS FD001 turbofan degradation dataset**.
FD001 contains multivariate run-to-failure histories for 100 training engines
and truncated histories for 100 test engines, with one operating condition,
one fault mode, sensor noise, and reference test RUL values. This focused subset
is sufficiently complex to demonstrate temporal predictive analysis while
remaining feasible for a solo capstone. [NASA describes the prediction task as
estimating the operational cycles remaining after each test trajectory ends.](https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data)

The selected algorithm is a **Random Forest regressor**. Each decision tree is
trained from a bootstrapped sample of engine observations and considers a
random subset of features at each split. The forest prediction is the mean of
its tree predictions. Combining diverse trees captures nonlinear interactions
between sensors while reducing the instability of a single decision tree.

![Proposed training and runtime flow.](images/algorithmic-component-flow.svg){width=100%}

### Processing and Behavior

1. Parse FD001 rows into engine, cycle, operating-setting, and sensor fields;
   reject malformed or incomplete records.
2. Label each training row with `RUL = final engine cycle - current cycle` and
   cap early-life RUL to reduce excessive influence from healthy observations.
3. Remove constant sensors and construct rolling-window statistics and trends
   for informative sensor channels. Fit all preprocessing on training engines
   only to prevent data leakage.
4. Split by engine identifier, never by individual row, so observations from
   one engine cannot appear in both training and validation sets.
5. Train a seeded Random Forest and evaluate engine-level predictions using
   mean absolute error (MAE) and root mean squared error (RMSE). Compare it with
   a simple median-RUL predictor and the existing SentinelOps risk baseline.
6. Persist the approved model, preprocessing metadata, selected features,
   training-data identifier, metrics, seed, and semantic model version.
7. At runtime, apply the same feature contract, predict RUL, derive a bounded
   risk and maintenance band, and store the result with workflow and model
   traceability before exposing it through current interfaces.

## Rationale and Implementation Strategy

**What it adds.** The algorithm changes SentinelOps from fixed threshold scoring
to prognostics learned from degradation trajectories. Users gain an estimated
maintenance horizon, model version, confidence context, and feature-importance
evidence in addition to the existing risk categories.

**How it fits.** Training and evaluation belong in `services/ml`; batch feature
preparation remains a Spark responsibility; Airflow coordinates training or
scoring; FastAPI and the dashboard consume stored predictions. The existing
prediction repository and workflow fingerprints provide an integration point
without coupling the model to presentation or orchestration code. The current
baseline remains available for comparison and fallback.

**Why this solution.** RUL regression matches predictive maintenance more
directly than a generic failure label. Random Forests support nonlinear sensor
relationships, require less tuning and compute than deep sequence models, and
provide feature importance that a reviewer can inspect. FD001 has an official
NASA source, known RUL targets, and constrained operating conditions. These
choices balance algorithmic significance, explainability, reproducibility, and
the remaining capstone schedule.

Implementation will begin only after instructor feedback. The first story will
add reproducible dataset acquisition and validation; the second will implement
feature construction, training, evaluation, and model metadata; the third will
integrate inference with SentinelOps scoring, storage, API, dashboard, and
end-to-end tests. Acceptance will require deterministic training with a fixed
seed, no engine leakage, documented MAE/RMSE against a naive baseline, exact
model/input traceability, and graceful fallback when an artifact or required
feature is unavailable.

Primary dataset references: [NASA Open Data](https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data)
and the [NASA Prognostics Center of Excellence repository](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/).
