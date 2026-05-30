# Spark Jobs

PySpark jobs for telemetry ingestion, ETL, feature engineering, and batch scoring support.

## Sprint 1 Usage

Sprint 1 uses a lightweight Python feature job so the vertical slice can run locally before introducing a full Spark runtime.

```bash
python3 -m services.spark_jobs.features \
  --input data/raw/telemetry_local-run.csv \
  --processed-dir data/processed
```

The job validates the raw telemetry contract, groups telemetry by run and asset, and writes demonstration-scale feature rows to `data/processed/features_<run_id>.csv` for later predictive scoring.
