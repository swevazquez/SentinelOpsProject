# Machine Learning Service

Training, evaluation, inference helpers, model metadata, and predictive maintenance artifacts.

## C-MAPSS FD001 Data Contract

`SCRUM-30` establishes the reproducible input contract for the approved
Remaining Useful Life algorithm. The acquisition command downloads NASA's
public C-MAPSS archive, verifies its pinned SHA-256 checksum, and extracts only
the FD001 source files:

```bash
python3 -m services.ml.cmapss acquire
```

The preparation command validates the 26-column FD001 schema, calculates each
training row's uncapped RUL as `final engine cycle - current cycle`, caps the
model target at 125 cycles, and creates a seeded 80/20 split by engine ID:

```bash
python3 -m services.ml.cmapss prepare
```

Generated source data is stored under `data/raw/cmapss/`; labeled training and
validation files are stored under `data/processed/cmapss-fd001/`. These paths
are intentionally excluded from Git. The generated metadata records the NASA
source, archive and training-file checksums, schema, RUL rule, split seed, and
the exact engine IDs assigned to each partition. Contract version `1.0.0`
defines `engine_id` and `cycle` as identifiers, three operating settings and 21
sensors as raw feature candidates, and `rul` as the capped model target while
retaining `rul_uncapped` for traceability. Feature selection and rolling feature
engineering are intentionally handled by the subsequent model-training story.

The committed fixture at `tests/fixtures/cmapss/train_FD001_sample.txt` exercises
the same parser and labeling pipeline without requiring network access in CI.

## Random Forest RUL Training and Evaluation

`SCRUM-31` implements the offline model-development stage. It reads the
engine-isolated partitions produced by the FD001 contract, selects informative
sensors using only the training engines, and creates causal rolling means,
rolling standard deviations, and sensor trends. Validation-engine values never
participate in fitted sensor selection.

The training command fits a seeded, 80-tree scikit-learn Random Forest
regressor with a maximum depth of 14 and
reports validation MAE and RMSE overall, by engine, and as an engine-level macro
average. The same metrics are reported for a median-training-RUL baseline:

```bash
uv run python -m services.ml.rul_training
```

The default versioned artifact is written to:

```text
data/models/rul-random-forest/1.0.0/
├── metadata.json
└── model.joblib
```

Generated model files are ignored by Git. `metadata.json` records the semantic
model version, dataset and contract identity, input hashes, split engine IDs,
seed, estimator configuration, selected and dropped sensors, complete temporal
feature list, feature importance, scikit-learn, NumPy, and joblib versions,
model checksum, and Random Forest and baseline metrics. Artifact versions are
immutable: choose a new semantic version instead of overwriting an existing
directory.

The verified default FD001 run used 80 training engines and 20 validation
engines. Its validation results were:

| Evaluation | MAE | RMSE |
| --- | ---: | ---: |
| Random Forest, all validation rows | 12.13 | 17.47 |
| Random Forest, macro average across engines | 12.46 | 16.46 |
| Median-RUL baseline, all validation rows | 35.27 | 43.73 |
| Median-RUL baseline, macro average across engines | 35.84 | 44.33 |

`SCRUM-31` trains and evaluates the model. Runtime inference and operational
persistence are described below; dashboard presentation remains a subsequent
Sprint 4 story.

## Versioned RUL Inference

`SCRUM-32` integrates the approved versioned artifact into the existing
predictive workflow. RUL mode validates the artifact schema, semantic model
version, dataset contract, ordered temporal feature contract, serialized payload,
feature count, and model checksum before loading the estimator. It accepts
C-MAPSS-compatible CSV trajectories with engine, cycle, setting, and sensor
fields; labels may be present but are not required for inference.

The runtime applies the exact selected-sensor and causal rolling-window contract
stored during training. It scores every observed cycle and persists the
latest-cycle estimate for each engine as a capped maintenance horizon from 0 to
125 cycles. The operational mapping is:

| Predicted RUL | Risk | Health | Status | Priority |
| ---: | ---: | ---: | --- | --- |
| `0` to `31.25` cycles | `0.75` to `1.00` | `0.00` to `0.25` | Critical | Immediate |
| `>31.25` to `62.50` cycles | `0.50` to `<0.75` | `>0.25` to `0.50` | Warning | High |
| `>62.50` to `93.75` cycles | `0.25` to `<0.50` | `>0.50` to `0.75` | Watch | Medium |
| `>93.75` to `125` cycles | `0.00` to `<0.25` | `>0.75` to `1.00` | Healthy | Routine |

Risk is `1 - (bounded RUL / 125)` and health is
`bounded RUL / 125`. Both are clamped to `[0, 1]`. Each stored result includes
the workflow run, prediction timestamp, input path and checksum, model name,
semantic model version and checksum, dataset identifier, serialized
feature-contract version, RUL, risk, health, status, priority, and recommended
action.

RUL inference is the default for `POST /api/workflows`, the dashboard, and
approved assistant actions. The repeatable scenario scores four held-out
engines at four lifecycle checkpoints and stores the run-specific, label-free
input used for each inference. The rule-based scorer remains available through
explicit `inference_mode: "baseline"` requests for local development and
testing. Missing, corrupt, or incompatible artifacts do not replace existing
prediction files.

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

## Prediction Traceability

`SCRUM-18` records the workflow run ID, processed feature path, and SHA-256
fingerprint with every prediction. The fingerprint identifies the exact feature
artifact used during file-based scoring and remains preserved when predictions
are stored and retrieved. In-memory scoring uses a deterministic fingerprint of
the canonical feature rows.
