from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from services.workflows.status import (
    get_workflow_status,
    list_workflow_statuses,
    record_workflow_status,
    summarize_workflow_statuses,
)


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

    def test_get_workflow_status_returns_structured_completed_state(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            record_workflow_status(
                project_root=project_root,
                run_id="completed-run",
                status="completed",
            )

            status = get_workflow_status(project_root, "completed-run")

        self.assertIsNotNone(status)
        assert status is not None
        self.assertEqual(status.run_id, "completed-run")
        self.assertEqual(status.status, "completed")
        self.assertIsNone(status.step)
        self.assertIsNone(status.error)

    def test_get_workflow_status_returns_failed_step_and_error_details(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            record_workflow_status(
                project_root=project_root,
                run_id="failed-run",
                status="failed",
                step="engineer_and_persist_features",
                error="feature processing failed",
            )

            status = get_workflow_status(project_root, "failed-run")

        self.assertIsNotNone(status)
        assert status is not None
        self.assertEqual(status.status, "failed")
        self.assertEqual(status.step, "engineer_and_persist_features")
        self.assertEqual(status.error, "feature processing failed")

    def test_get_workflow_status_returns_none_for_unknown_run(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            self.assertIsNone(get_workflow_status(project_root, "missing-run"))

    def test_list_workflow_statuses_returns_newest_first(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            status_dir = project_root / "data" / "workflow-status"
            status_dir.mkdir(parents=True)
            (status_dir / "workflow_old.json").write_text(
                json.dumps(
                    {
                        "run_id": "old",
                        "status": "completed",
                        "updated_at": "2026-06-26T10:00:00Z",
                        "step": None,
                        "error": None,
                    }
                ),
                encoding="utf-8",
            )
            (status_dir / "workflow_new.json").write_text(
                json.dumps(
                    {
                        "run_id": "new",
                        "status": "running",
                        "updated_at": "2026-06-26T11:00:00Z",
                        "step": "generate_and_persist_raw",
                        "error": None,
                    }
                ),
                encoding="utf-8",
            )

            statuses = list_workflow_statuses(project_root)

        self.assertEqual([status.run_id for status in statuses], ["new", "old"])

    def test_summarize_workflow_statuses_counts_states(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            record_workflow_status(
                project_root=project_root,
                run_id="running-run",
                status="running",
            )
            record_workflow_status(
                project_root=project_root,
                run_id="completed-run",
                status="completed",
            )
            record_workflow_status(
                project_root=project_root,
                run_id="failed-run",
                status="failed",
                error="failed",
            )

            summary = summarize_workflow_statuses(project_root)

        self.assertEqual(summary.total, 3)
        self.assertEqual(summary.running, 1)
        self.assertEqual(summary.completed, 1)
        self.assertEqual(summary.failed, 1)

    def test_get_workflow_status_rejects_unsafe_run_id(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            with self.assertRaisesRegex(ValueError, "file-safe"):
                get_workflow_status(project_root, "../other")

    def test_list_workflow_statuses_rejects_malformed_status_file(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            status_dir = project_root / "data" / "workflow-status"
            status_dir.mkdir(parents=True)
            (status_dir / "workflow_bad.json").write_text(
                json.dumps(
                    {
                        "run_id": "bad",
                        "status": "stalled",
                        "updated_at": "2026-06-26T11:00:00Z",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "unsupported workflow status"):
                list_workflow_statuses(project_root)


if __name__ == "__main__":
    unittest.main()
