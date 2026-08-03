# Airflow DAGs

SentinelOps uses Airflow for visible, repeatable pipeline coordination. The DAGs
delegate feature preparation, model inference, persistence, and status handling to
the reusable service modules; they do not duplicate those rules inside task code.

## Available DAGs

| DAG | Purpose | Schedule |
|---|---|---|
| `sentinelops_sprint1_pipeline` | Generate representative telemetry and persist Sprint 1 feature output. | Manual only |
| `sentinelops_predictive_maintenance` | Select a RUL trajectory, invoke the Spark batch boundary, persist traceable predictions, and finalize workflow status. | Manual only |

## Final predictive-maintenance workflow

Trigger `sentinelops_predictive_maintenance` manually from Airflow. The default
input selection uses the next held-out FD001 lifecycle checkpoint from the
repeatable RUL demo scenario. Set `SENTINELOPS_AIRFLOW_INPUT_PATH` to a
C-MAPSS-compatible CSV when a reviewer needs to run a specific input instead.
The model version defaults to `1.0.0` and can be changed with
`SENTINELOPS_AIRFLOW_MODEL_VERSION`.

The task sequence is:

1. `select_predictive_input` selects the configured trajectory or reserves the next demo checkpoint.
2. `run_spark_rul_batch` invokes `services.spark_jobs.rul_batch.run_spark_rul_batch`.
3. `finalize_predictive_workflow` advances the demo checkpoint and records completion.

The DAG is manual-only (`schedule=None`) so a demonstration run cannot silently
advance the RUL scenario. Failures release a reserved checkpoint and write a
sanitized failed status with the run ID and failed task.
