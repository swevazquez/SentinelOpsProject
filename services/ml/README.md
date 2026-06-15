# Machine Learning Service

Training, evaluation, inference helpers, model metadata, and predictive maintenance artifacts.

## Predictive Scoring

`SCRUM-6` provides a deterministic, explainable baseline scorer for the
demonstration-scale Sprint 2 workflow. It validates processed feature rows and
generates one bounded risk score per asset with the workflow run ID and model
metadata. `SCRUM-7` enriches each prediction with an asset status, maintenance
priority, and recommended action:

| Risk score | Asset status | Maintenance priority |
| --- | --- | --- |
| `0.75` to `1.00` | Critical | Immediate |
| `0.50` to `< 0.75` | Warning | High |
| `0.25` to `< 0.50` | Watch | Medium |
| `0.00` to `< 0.25` | Healthy | Routine |

```bash
python3 -m services.ml.scoring \
  --input data/processed/features_local-run.csv
```

The command prints prediction results and maintenance indicators as JSON.

## Prediction Storage

`SCRUM-8` provides a `PredictionRepository` contract and a local CSV
implementation for the demonstration-scale workflow. Prediction batches are
stored by workflow run under `data/predictions/` and can be retrieved by run ID
or asset ID. The full scoring result is preserved for later API and dashboard
access.

The repository boundary allows the planned PostgreSQL implementation to replace
local CSV storage without changing scoring or API callers.
