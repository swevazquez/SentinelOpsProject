from datetime import UTC, datetime
import unittest

from services.ml.scoring import (
    MODEL_NAME,
    MODEL_VERSION,
    calculate_risk_score,
    maintenance_indicators,
    score_feature_rows,
)


def feature_row(
    *,
    asset_id: str = "A-100",
    run_id: str = "scoring-run",
    max_temperature_c: str = "75.00",
    max_vibration_mm_s: str = "3.00",
    avg_pressure_kpa: str = "225.00",
    max_runtime_hours: str = "1500",
    failure_observed: str = "0",
) -> dict[str, str]:
    return {
        "run_id": run_id,
        "asset_id": asset_id,
        "max_temperature_c": max_temperature_c,
        "max_vibration_mm_s": max_vibration_mm_s,
        "avg_pressure_kpa": avg_pressure_kpa,
        "max_runtime_hours": max_runtime_hours,
        "failure_observed": failure_observed,
    }


class PredictiveScoringTests(unittest.TestCase):
    def test_score_feature_rows_generates_one_prediction_per_asset(self):
        scored_at = datetime(2026, 6, 15, 15, 30, tzinfo=UTC)

        predictions = score_feature_rows(
            [
                feature_row(asset_id="A-101"),
                feature_row(asset_id="A-100"),
            ],
            scored_at=scored_at,
        )

        self.assertEqual(
            [prediction["asset_id"] for prediction in predictions],
            ["A-100", "A-101"],
        )
        self.assertEqual(
            {prediction["run_id"] for prediction in predictions},
            {"scoring-run"},
        )
        self.assertEqual(
            {prediction["model_name"] for prediction in predictions},
            {MODEL_NAME},
        )
        self.assertEqual(
            {prediction["model_version"] for prediction in predictions},
            {MODEL_VERSION},
        )
        self.assertEqual(
            {prediction["scored_at"] for prediction in predictions},
            {"2026-06-15T15:30:00Z"},
        )
        self.assertEqual(
            {prediction["source_feature_path"] for prediction in predictions},
            {"in-memory"},
        )
        self.assertEqual(
            {len(prediction["source_feature_sha256"]) for prediction in predictions},
            {64},
        )
        self.assertTrue(
            all(prediction["asset_status"] for prediction in predictions)
        )
        self.assertTrue(
            all(prediction["maintenance_priority"] for prediction in predictions)
        )
        self.assertTrue(
            all(prediction["recommended_action"] for prediction in predictions)
        )

    def test_calculate_risk_score_increases_for_degraded_asset_features(self):
        healthy_score = calculate_risk_score(feature_row())
        degraded_score = calculate_risk_score(
            feature_row(
                max_temperature_c="94.00",
                max_vibration_mm_s="7.20",
                avg_pressure_kpa="268.00",
                max_runtime_hours="3400",
                failure_observed="1",
            )
        )

        self.assertGreater(degraded_score, healthy_score)
        self.assertGreaterEqual(healthy_score, 0.0)
        self.assertLessEqual(degraded_score, 1.0)

    def test_score_feature_rows_rejects_missing_fields(self):
        row = feature_row()
        del row["max_vibration_mm_s"]

        with self.assertRaisesRegex(ValueError, "missing required scoring fields"):
            score_feature_rows([row])

    def test_score_feature_rows_rejects_mixed_workflow_runs(self):
        with self.assertRaisesRegex(ValueError, "one workflow run_id"):
            score_feature_rows(
                [
                    feature_row(asset_id="A-100", run_id="run-1"),
                    feature_row(asset_id="A-101", run_id="run-2"),
                ]
            )

    def test_score_feature_rows_rejects_duplicate_assets(self):
        with self.assertRaisesRegex(ValueError, "one row per asset"):
            score_feature_rows([feature_row(), feature_row()])

    def test_score_feature_rows_produces_stable_input_fingerprint(self):
        first = score_feature_rows(
            [
                feature_row(asset_id="A-101"),
                feature_row(asset_id="A-100"),
            ]
        )
        second = score_feature_rows(
            [
                feature_row(asset_id="A-100"),
                feature_row(asset_id="A-101"),
            ]
        )

        self.assertEqual(
            first[0]["source_feature_sha256"],
            second[0]["source_feature_sha256"],
        )

    def test_maintenance_indicators_cover_priority_thresholds(self):
        cases = [
            (0.0, "healthy", "routine"),
            (0.25, "watch", "medium"),
            (0.50, "warning", "high"),
            (0.75, "critical", "immediate"),
            (1.0, "critical", "immediate"),
        ]

        for risk_score, expected_status, expected_priority in cases:
            with self.subTest(risk_score=risk_score):
                indicators = maintenance_indicators(risk_score)
                self.assertEqual(indicators["asset_status"], expected_status)
                self.assertEqual(
                    indicators["maintenance_priority"],
                    expected_priority,
                )
                self.assertTrue(indicators["recommended_action"])


if __name__ == "__main__":
    unittest.main()
