from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from services.ml.prediction_store import prediction_repository
from services.spark_jobs.rul_batch import main
from tests.rul_test_support import prepare_rul_runtime


class SparkCommandLineSystemTests(unittest.TestCase):
    def test_documented_local_command_runs_without_external_cluster(self) -> None:
        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ,
            {"SENTINELOPS_PERSISTENCE_BACKEND": "file"},
            clear=False,
        ):
            project_root = Path(temp_dir)
            prepare_rul_runtime(project_root)
            output = StringIO()
            arguments = [
                "rul_batch",
                "--project-root",
                str(project_root),
                "--input",
                "data/processed/cmapss-fd001/validation.csv",
                "--run-id",
                "spark-cli",
                "--model-version",
                "1.0.0",
                "--master",
                "local[2]",
            ]

            with patch("sys.argv", arguments), redirect_stdout(output):
                main()

            predictions = prediction_repository(project_root).get_by_run(
                "spark-cli"
            )

        self.assertIn("Spark RUL batch completed run_id=spark-cli", output.getvalue())
        self.assertEqual(len(predictions), 2)


if __name__ == "__main__":
    unittest.main()
