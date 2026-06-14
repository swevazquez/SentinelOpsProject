from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATHS = (
    ".env.example",
    "data/samples/asset_profiles.csv",
    "scripts/check-prerequisites.sh",
    "scripts/seed-data.sh",
    "scripts/setup.sh",
    "services",
)


class CleanCheckoutTests(unittest.TestCase):
    def test_setup_is_idempotent_and_workflow_creates_expected_artifacts(self):
        with TemporaryDirectory() as temp_dir:
            checkout = Path(temp_dir) / "repo"
            checkout.mkdir()
            for relative_path in FIXTURE_PATHS:
                source = PROJECT_ROOT / relative_path
                destination = checkout / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                if source.is_dir():
                    shutil.copytree(source, destination)
                else:
                    shutil.copy2(source, destination)

            environment = os.environ.copy()
            environment["PYTHON_BIN"] = sys.executable

            first_setup = subprocess.run(
                ["./scripts/setup.sh"],
                cwd=checkout,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
            env_path = checkout / ".env"
            env_path.write_text(
                env_path.read_text(encoding="utf-8") + "\nLOCAL_MARKER=preserve\n",
                encoding="utf-8",
            )
            second_setup = subprocess.run(
                ["./scripts/setup.sh"],
                cwd=checkout,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
            workflow = subprocess.run(
                ["./scripts/seed-data.sh", "clean-checkout"],
                cwd=checkout,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )

            status_path = (
                checkout
                / "data"
                / "workflow-status"
                / "workflow_clean-checkout.json"
            )
            status = json.loads(status_path.read_text(encoding="utf-8"))

            self.assertIn("Created .env from .env.example", first_setup.stdout)
            self.assertIn("Existing .env preserved", second_setup.stdout)
            self.assertIn("LOCAL_MARKER=preserve", env_path.read_text(encoding="utf-8"))
            self.assertTrue(
                (checkout / "data/raw/telemetry_clean-checkout.csv").is_file()
            )
            self.assertTrue(
                (checkout / "data/processed/features_clean-checkout.csv").is_file()
            )
            self.assertEqual(status["run_id"], "clean-checkout")
            self.assertEqual(status["status"], "completed")
            self.assertIn(
                "Sprint 1 workflow completed for run clean-checkout",
                workflow.stdout,
            )

    def test_prerequisite_check_reports_missing_python(self):
        environment = os.environ.copy()
        environment["PYTHON_BIN"] = "missing-python-command"

        result = subprocess.run(
            ["./scripts/check-prerequisites.sh"],
            cwd=PROJECT_ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Python 3.12 or later was not found", result.stderr)


if __name__ == "__main__":
    unittest.main()
