# Sprint 1 Workflow Design

Sprint 1 establishes the first working SentinelOps vertical slice. The workflow intentionally stays narrow: generate representative telemetry, persist raw data, engineer features, and make the sequence runnable through Airflow.

## Workflow Steps

1. `services.simulator.telemetry` loads representative asset profiles from `data/samples/asset_profiles.csv` and generates deterministic hourly telemetry.
2. Raw telemetry rows are validated and persisted to `data/raw/telemetry_<run_id>.csv`.
3. `services.spark_jobs.features` validates the raw telemetry contract and groups telemetry by `run_id` and `asset_id`.
4. Processed feature rows are validated and persisted to `data/processed/features_<run_id>.csv`.
5. `airflow/dags/sentinelops_sprint1_pipeline.py` coordinates the generation and feature-processing tasks.

## Raw Telemetry Contract

Raw telemetry storage uses CSV files under `data/raw/`. Each file is named from the workflow or generation run identifier:

```text
data/raw/telemetry_<run_id>.csv
```

Before storage, the simulator verifies that the generated row set is non-empty, has a single non-empty `run_id`, and contains all required telemetry fields.

| Field | Description |
|---|---|
| `run_id` | Workflow or generation run identifier |
| `asset_id` | Representative asset identifier |
| `timestamp` | UTC ISO timestamp for the sample |
| `temperature_c` | Simulated temperature reading |
| `vibration_mm_s` | Simulated vibration reading |
| `pressure_kpa` | Simulated pressure reading |
| `runtime_hours` | Simulated cumulative runtime |
| `failure_within_7d` | Demonstration label for near-term failure risk |

## Feature Output Contract

Processed feature storage uses CSV files under `data/processed/`. Each file is named from the source run identifier:

```text
data/processed/features_<run_id>.csv
```

Feature processing requires the raw telemetry schema, rejects empty raw input, and creates one feature row per `run_id` and `asset_id`.

| Field | Description |
|---|---|
| `run_id` | Source workflow or generation run |
| `asset_id` | Asset represented by the feature row |
| `sample_count` | Number of raw telemetry samples used |
| `first_timestamp` | Earliest source telemetry timestamp for the asset |
| `last_timestamp` | Latest source telemetry timestamp for the asset |
| `avg_temperature_c` | Average temperature across samples |
| `max_temperature_c` | Maximum temperature across samples |
| `avg_vibration_mm_s` | Average vibration across samples |
| `max_vibration_mm_s` | Maximum vibration across samples |
| `avg_pressure_kpa` | Average pressure across samples |
| `min_runtime_hours` | Minimum observed runtime |
| `max_runtime_hours` | Maximum observed runtime |
| `failure_observed` | Whether any source sample had a positive failure label |

## Local Validation

Run the local data slice:

```bash
./scripts/seed-data.sh sprint1-smoke
```

Run unit tests:

```bash
python3 -m unittest discover -s tests
```

This workflow satisfies the Sprint 1 foundation for telemetry generation, raw data persistence, feature engineering, and orchestration readiness. Predictive scoring is intentionally deferred to Sprint 2.
