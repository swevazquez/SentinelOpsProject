# Spark Jobs

SentinelOps provides a local PySpark batch path for C-MAPSS input preparation,
versioned RUL inference, and shared persistence. The implementation targets a
single-node capstone demonstration rather than a distributed production cluster.

## RUL Batch Usage

Install the Spark dependency and ensure Java 17 or later is available:

```bash
uv sync --extra dev --extra spark
```

After preparing FD001 and training model version `1.0.0`, run from the repository
root:

```bash
uv run --extra spark python -m services.spark_jobs.rul_batch \
  --project-root . \
  --input data/processed/cmapss-fd001/validation.csv \
  --run-id spark-local-review \
  --model-version 1.0.0 \
  --master 'local[2]'
```

The supported application boundary is
`services.spark_jobs.rul_batch.run_spark_rul_batch`. The final Airflow DAG can
call this function or its command-line wrapper without copying feature, model,
or persistence logic into the DAG.

The job performs the following sequence:

1. Spark reads the C-MAPSS-compatible CSV and verifies required columns.
2. Spark casts numeric values, rejects invalid identifiers and duplicate cycles,
   verifies contiguous engine histories, and deterministically orders the batch.
3. The existing ML service loads the versioned artifact, applies its temporal
   feature contract, and calculates RUL and maintenance indicators.
4. The shared repository selected by `SENTINELOPS_PERSISTENCE_BACKEND` commits
   predictions to file storage or PostgreSQL.
5. Shared workflow status records running, completed, or failed state with the
   active Spark step.

Failures before persistence do not replace the last committed prediction set.
The job preserves the input fingerprint, run and asset identifiers, model and
dataset versions, feature-contract version, and prediction timestamp.

## Sprint 1 Usage

Sprint 1 retains its lightweight Python feature job for the original baseline
workflow and regression tests.

```bash
python3 -m services.spark_jobs.features \
  --input data/raw/telemetry_local-run.csv \
  --processed-dir data/processed
```

The job validates the raw telemetry contract, groups telemetry by run and asset, and writes demonstration-scale feature rows to `data/processed/features_<run_id>.csv` for later predictive scoring.
