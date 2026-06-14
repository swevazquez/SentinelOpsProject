from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


DAG_PATH = Path("airflow/dags/sentinelops_sprint1_pipeline.py")


def _load_dag_module():
    airflow_module = ModuleType("airflow")
    decorators_module = ModuleType("airflow.decorators")

    def dag(**_kwargs):
        return lambda _function: lambda: None

    def task(function):
        return function

    decorators_module.dag = dag
    decorators_module.task = task
    airflow_module.decorators = decorators_module

    spec = importlib.util.spec_from_file_location(
        "sentinelops_sprint1_pipeline_test",
        DAG_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load DAG module from {DAG_PATH}")

    module = importlib.util.module_from_spec(spec)
    with patch.dict(
        sys.modules,
        {
            "airflow": airflow_module,
            "airflow.decorators": decorators_module,
        },
    ):
        spec.loader.exec_module(module)
    return module


class AirflowFailureReportingTests(unittest.TestCase):
    def test_failure_callback_uses_shared_status_reporter(self):
        module = _load_dag_module()

        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            module.PROJECT_ROOT = project_root
            context = {
                "dag_run": SimpleNamespace(run_id="airflow-failed-run"),
                "task_instance": SimpleNamespace(task_id="engineer_feature_output"),
                "exception": RuntimeError("invalid raw telemetry"),
            }

            with self.assertLogs("services.workflows.status", level="ERROR"):
                module.report_workflow_failure(context)

            status_path = (
                project_root
                / "data"
                / "workflow-status"
                / "workflow_airflow-failed-run.json"
            )
            status_record = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertEqual(status_record["run_id"], "airflow-failed-run")
        self.assertEqual(status_record["status"], "failed")
        self.assertEqual(status_record["step"], "engineer_feature_output")
        self.assertEqual(status_record["error"], "invalid raw telemetry")


if __name__ == "__main__":
    unittest.main()
