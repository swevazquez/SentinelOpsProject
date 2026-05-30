# Telemetry Simulator

Telemetry simulator for generating realistic sample asset sensor data for local development and demonstrations.

## Sprint 1 Usage

Generate deterministic representative telemetry:

```bash
python3 -m services.simulator.telemetry \
  --run-id local-run \
  --hours 24 \
  --output data/raw/telemetry_local-run.csv
```

The output CSV is the raw telemetry handoff for feature engineering.
