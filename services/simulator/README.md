# Telemetry Simulator

Telemetry simulator for generating realistic sample asset sensor data for local development and demonstrations.

## Sprint 1 Usage

Generate deterministic representative telemetry:

```bash
python3 -m services.simulator.telemetry \
  --run-id local-run \
  --hours 24 \
  --asset-config data/samples/asset_profiles.csv \
  --raw-dir data/raw
```

The simulator reads representative asset profiles from `data/samples/asset_profiles.csv`.
The output CSV is persisted as `data/raw/telemetry_<run_id>.csv` and becomes the raw telemetry handoff for feature engineering.
