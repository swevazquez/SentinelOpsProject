CREATE TABLE IF NOT EXISTS sentinelops_predictions (
    run_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    prediction_type TEXT NOT NULL,
    scored_at TEXT NOT NULL,
    payload JSONB NOT NULL,
    PRIMARY KEY (run_id, asset_id)
);

CREATE INDEX IF NOT EXISTS sentinelops_predictions_asset_scored_idx
    ON sentinelops_predictions (asset_id, scored_at DESC);

CREATE TABLE IF NOT EXISTS sentinelops_workflow_status (
    run_id TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
    updated_at TEXT NOT NULL,
    step TEXT,
    error TEXT,
    approval_id TEXT
);

CREATE INDEX IF NOT EXISTS sentinelops_workflow_updated_idx
    ON sentinelops_workflow_status (updated_at DESC);
