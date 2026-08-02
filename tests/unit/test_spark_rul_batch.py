from __future__ import annotations

from pathlib import Path
import unittest

from services.spark_jobs.rul_batch import (
    SparkRulBatchConfig,
    _sanitized_error,
    _validate_config,
)


class SparkRulBatchConfigurationTests(unittest.TestCase):
    def test_configuration_requires_safe_run_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "file-safe"):
            _validate_config(
                SparkRulBatchConfig(
                    project_root=Path("."),
                    input_path=Path("trajectory.csv"),
                    run_id="../unsafe",
                )
            )

    def test_configuration_requires_semantic_model_version(self) -> None:
        with self.assertRaisesRegex(ValueError, "semantic"):
            _validate_config(
                SparkRulBatchConfig(
                    project_root=Path("."),
                    input_path=Path("trajectory.csv"),
                    run_id="spark-run",
                    model_version="latest",
                )
            )

    def test_failure_message_removes_database_credentials(self) -> None:
        error = RuntimeError(
            "could not connect postgresql://sentinelops:secret@postgres/db"
        )

        message = _sanitized_error(error)

        self.assertNotIn("secret", message)
        self.assertIn("postgresql://***@postgres/db", message)


if __name__ == "__main__":
    unittest.main()
