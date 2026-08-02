from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
import sys
import unittest
from unittest.mock import patch

from services.workflows.airflow_pipeline import (
    select_predictive_input,
    report_airflow_failure,
)


DAG_PATH = Path("airflow/dags/sentinelops_predictive_maintenance.py")


def _load_dag_module():
    airflow_module = ModuleType("airflow")
    decorators_module = ModuleType("airflow.decorators")
    calls: list[str] = []
    dag_options: dict[str, object] = {}

    class FakeXComArg:
        pass

    class FakeTask:
        def __init__(self, function):
            self.function = function

        def __call__(self, *_args, **_kwargs):
            calls.append(self.function.__name__)
            return FakeXComArg()

    def task(function=None, **_kwargs):
        if function is not None:
            return FakeTask(function)
        return lambda decorated: FakeTask(decorated)

    def dag(**kwargs):
        dag_options.update(kwargs)
        return lambda function: function

    decorators_module.dag = dag
    decorators_module.task = task
    airflow_module.decorators = decorators_module

    spec = importlib.util.spec_from_file_location(
        "sentinelops_predictive_maintenance_test",
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
    return module, calls, dag_options


class AirflowPipelineTests(unittest.TestCase):
    def test_configured_input_is_selected_without_reserving_demo_checkpoint(self):
        with TemporaryDirectory() as temp_dir, patch.dict(
            "os.environ",
            {"SENTINELOPS_PERSISTENCE_BACKEND": "file"},
            clear=False,
        ):
            project_root = Path(temp_dir)
            input_path = project_root / "data" / "input.csv"
            input_path.parent.mkdir(parents=True)
            input_path.write_text("engine_id,cycle\n1,1\n", encoding="utf-8")

            selection = select_predictive_input(
                project_root=project_root,
                run_id="airflow-configured-input",
                input_path=input_path,
            )
            status_path = (
                project_root
                / "data"
                / "workflow-status"
                / "workflow_airflow-configured-input.json"
            )
            status_record = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertEqual(selection["input_path"], "data/input.csv")
        self.assertFalse(selection["demo_reserved"])
        self.assertIsNone(selection["checkpoint_number"])
        self.assertEqual(status_record["step"], "airflow_input_selection")

    def test_failure_callback_sanitizes_error_and_records_failed_step(self):
        with TemporaryDirectory() as temp_dir:
            with patch(
                "services.workflows.airflow_pipeline.release_rul_demo_run"
            ) as release, patch(
                "services.workflows.airflow_pipeline.record_workflow_status"
            ) as record:
                report_airflow_failure(
                    {
                        "dag_run": SimpleNamespace(run_id="airflow-failed"),
                        "task_instance": SimpleNamespace(task_id="run_spark_rul_batch"),
                        "exception": RuntimeError(
                            "connection failed: postgresql://user:secret@postgres/db"
                        ),
                    },
                    project_root=Path(temp_dir),
                )

        release.assert_called_once()
        record.assert_called_once()
        self.assertEqual(record.call_args.kwargs["status"], "failed")
        self.assertEqual(record.call_args.kwargs["step"], "run_spark_rul_batch")
        self.assertIn("postgresql://***@postgres/db", record.call_args.kwargs["error"])
        self.assertNotIn("secret", record.call_args.kwargs["error"])

    def test_final_dag_exposes_ordered_tasks_and_manual_schedule(self):
        _module, calls, dag_options = _load_dag_module()

        self.assertEqual(
            calls,
            ["select_input", "run_spark_batch", "finalize_workflow"],
        )
        self.assertEqual(dag_options["dag_id"], "sentinelops_predictive_maintenance")
        self.assertIsNone(dag_options["schedule"])
        self.assertFalse(dag_options["catchup"])


if __name__ == "__main__":
    unittest.main()
