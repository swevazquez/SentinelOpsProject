from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from services.ml.scoring import score_feature_file
from services.simulator.telemetry import (
    generate_telemetry,
    load_asset_profiles,
    persist_raw_telemetry,
)
from services.spark_jobs.features import engineer_features, persist_feature_rows


ASSET_CONFIG = "\n".join(
    [
        "asset_id,base_temperature_c,base_vibration_mm_s,base_pressure_kpa,runtime_hours,failure_risk",
        "TEST-1,70.0,2.5,220.0,100,0.1",
        "TEST-2,84.0,5.5,248.0,2600,0.6",
    ]
)


class PredictiveScoringIntegrationTests(unittest.TestCase):
    def test_processed_features_generate_predictions_for_associated_assets(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            config_path = project_root / "data" / "samples" / "asset_profiles.csv"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(ASSET_CONFIG, encoding="utf-8")

            telemetry_rows = generate_telemetry(
                run_id="sprint2-run",
                start_time=datetime(2026, 6, 15, tzinfo=UTC),
                hours=4,
                seed=12,
                assets=load_asset_profiles(config_path),
            )
            raw_result = persist_raw_telemetry(
                telemetry_rows,
                project_root / "data" / "raw",
            )
            feature_result = persist_feature_rows(
                engineer_features(raw_result.path),
                project_root / "data" / "processed",
            )

            predictions = score_feature_file(
                feature_result.path,
                scored_at=datetime(2026, 6, 15, 16, 0, tzinfo=UTC),
            )

        self.assertEqual(len(predictions), 2)
        self.assertEqual(
            {prediction["asset_id"] for prediction in predictions},
            {"TEST-1", "TEST-2"},
        )
        self.assertEqual(
            {prediction["run_id"] for prediction in predictions},
            {"sprint2-run"},
        )
        self.assertTrue(
            all(0.0 <= float(prediction["risk_score"]) <= 1.0 for prediction in predictions)
        )


if __name__ == "__main__":
    unittest.main()
