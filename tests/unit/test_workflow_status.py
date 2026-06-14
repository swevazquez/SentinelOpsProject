from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from services.workflows.status import record_workflow_status


class WorkflowStatusTests(unittest.TestCase):
    def test_record_workflow_status_persists_structured_data_and_logs_state(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            with self.assertLogs("services.workflows.status", level="INFO") as logs:
                output_path = record_workflow_status(
                    project_root=project_root,
                    run_id="status-test",
                    status="running",
                    step="generate_and_persist_raw",
                )

            record = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(record["run_id"], "status-test")
        self.assertEqual(record["status"], "running")
        self.assertEqual(record["step"], "generate_and_persist_raw")
        self.assertIsNone(record["error"])
        self.assertTrue(record["updated_at"].endswith("Z"))
        self.assertIn("run_id=status-test", logs.output[0])
        self.assertIn("status=running", logs.output[0])


if __name__ == "__main__":
    unittest.main()
