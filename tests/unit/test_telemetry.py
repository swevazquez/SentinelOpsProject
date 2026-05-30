from datetime import UTC, datetime
import unittest

from services.simulator.telemetry import DEFAULT_ASSETS, TELEMETRY_FIELDS, generate_telemetry


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


if __name__ == "__main__":
    unittest.main()
