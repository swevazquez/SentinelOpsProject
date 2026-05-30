from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from services.simulator.telemetry import (
    DEFAULT_ASSETS,
    TELEMETRY_FIELDS,
    generate_telemetry,
    load_asset_profiles,
)


class TelemetryGenerationTests(unittest.TestCase):
    def test_generate_telemetry_creates_hourly_rows_for_each_asset(self):
        rows = generate_telemetry(
            run_id="test-run",
            start_time=datetime(2026, 5, 17, tzinfo=UTC),
            hours=2,
            seed=7,
        )

        self.assertEqual(len(rows), len(DEFAULT_ASSETS) * 2)
        self.assertEqual(set(rows[0].keys()), set(TELEMETRY_FIELDS))
        self.assertEqual({row["run_id"] for row in rows}, {"test-run"})
        self.assertEqual(
            {row["asset_id"] for row in rows},
            {asset.asset_id for asset in DEFAULT_ASSETS},
        )

    def test_generate_telemetry_rejects_non_positive_hours(self):
        with self.assertRaisesRegex(ValueError, "hours"):
            generate_telemetry(
                run_id="test-run",
                start_time=datetime(2026, 5, 17, tzinfo=UTC),
                hours=0,
            )

    def test_load_asset_profiles_reads_configured_assets(self):
        profiles = load_asset_profiles(Path("data/samples/asset_profiles.csv"))

        self.assertEqual(len(profiles), 4)
        self.assertEqual(profiles[0].asset_id, "A-100")
        self.assertEqual(profiles[-1].failure_risk, 0.58)

    def test_generate_telemetry_uses_configured_assets(self):
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "asset_profiles.csv"
            config_path.write_text(
                "\n".join(
                    [
                        "asset_id,base_temperature_c,base_vibration_mm_s,base_pressure_kpa,runtime_hours,failure_risk",
                        "CUSTOM-1,70.0,2.5,220.0,100,0.1",
                    ]
                ),
                encoding="utf-8",
            )

            rows = generate_telemetry(
                run_id="configured-run",
                start_time=datetime(2026, 5, 17, tzinfo=UTC),
                hours=3,
                seed=7,
                assets=load_asset_profiles(config_path),
            )

        self.assertEqual(len(rows), 3)
        self.assertEqual({row["asset_id"] for row in rows}, {"CUSTOM-1"})

    def test_load_asset_profiles_rejects_invalid_failure_risk(self):
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "asset_profiles.csv"
            config_path.write_text(
                "\n".join(
                    [
                        "asset_id,base_temperature_c,base_vibration_mm_s,base_pressure_kpa,runtime_hours,failure_risk",
                        "BAD-1,70.0,2.5,220.0,100,1.2",
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "failure_risk"):
                load_asset_profiles(config_path)


if __name__ == "__main__":
    unittest.main()
