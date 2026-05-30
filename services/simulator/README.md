# Telemetry Simulator

Telemetry simulator for generating realistic sample asset sensor data for local development and demonstrations.

## Sprint 1 Usage

Generate deterministic representative telemetry:

```bash
python3 -m services.simulator.telemetry \
  --run-id local-run \
  --hours 24 \
  --asset-config data/samples/asset_profiles.csv \
  --output data/raw/telemetry_local-run.csv
```

The simulator reads representative asset profiles from `data/samples/asset_profiles.csv`.
The output CSV is the raw telemetry handoff for feature engineering.
