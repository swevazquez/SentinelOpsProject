# Spark Jobs

PySpark jobs for telemetry ingestion, ETL, feature engineering, and batch scoring support.

## Sprint 1 Usage

Sprint 1 uses a lightweight Python feature job so the vertical slice can run locally before introducing a full Spark runtime.

```bash
python3 -m services.spark_jobs.features \
  --input data/raw/telemetry_local-run.csv \
  --output data/processed/features_local-run.csv
```

The job groups raw telemetry by run and asset and writes demonstration-scale feature rows for later predictive scoring.
