from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from services.agent.tools import (
    APPROVED_TOOLS,
    execute_tool,
    response_tool_schemas,
    tool_schemas,
)
from services.ml.prediction_store import CsvPredictionRepository
from services.ml.scoring import score_feature_rows
from services.workflows.status import record_workflow_status


class AgentToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temporary_directory.name)
        sample_dir = self.project_root / "data" / "samples"
        sample_dir.mkdir(parents=True)
        with (sample_dir / "asset_profiles.csv").open("w", newline="") as output:
            writer = csv.writer(output)
            writer.writerow(
                [
                    "asset_id",
                    "base_temperature_c",
                    "base_vibration_mm_s",
                    "base_pressure_kpa",
                    "runtime_hours",
                    "failure_risk",
                ]
            )
            writer.writerow(["PUMP-1", "60", "1.5", "220", "500", "0.1"])
        record_workflow_status(
            project_root=self.project_root,
            run_id="run-1",
            status="completed",
        )
        predictions = score_feature_rows(
            [
                {
                    "run_id": "run-1",
                    "asset_id": "PUMP-1",
                    "max_temperature_c": "60",
                    "max_vibration_mm_s": "1.5",
                    "avg_pressure_kpa": "220",
                    "max_runtime_hours": "500",
                    "failure_observed": "0",
                }
            ]
        )
        CsvPredictionRepository(self.project_root / "data" / "predictions").save(
            predictions
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_all_approved_tools_are_read_only_and_have_closed_schemas(self) -> None:
        self.assertTrue(APPROVED_TOOLS)
        self.assertTrue(all(tool.read_only for tool in APPROVED_TOOLS))
        self.assertTrue(
            all(
                schema["function"]["parameters"]["additionalProperties"] is False
                for schema in tool_schemas()
            )
        )
        self.assertTrue(all(schema["strict"] for schema in response_tool_schemas()))
        self.assertTrue(
            all("function" not in schema for schema in response_tool_schemas())
        )

    def test_approved_tools_return_structured_operational_data(self) -> None:
        scenarios = (
            ("list_assets", {}, "assets"),
            ("list_workflows", {}, "workflows"),
            ("get_latest_predictions", {}, "predictions"),
            ("get_workflow", {"run_id": "run-1"}, "workflow"),
            ("get_predictions_by_run", {"run_id": "run-1"}, "predictions"),
            (
                "get_predictions_by_asset",
                {"asset_id": "PUMP-1"},
                "predictions",
            ),
        )
        for tool_name, arguments, expected_key in scenarios:
            with self.subTest(tool_name=tool_name):
                response = execute_tool(
                    project_root=self.project_root,
                    tool_name=tool_name,
                    arguments=arguments,
                )
                self.assertEqual(response["status_code"], 200)
                self.assertTrue(response["read_only"])
                self.assertIn(expected_key, response["result"]["data"])

    def test_unknown_tool_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "not approved"):
            execute_tool(
                project_root=self.project_root,
                tool_name="run_workflow",
                arguments={},
            )

    def test_missing_or_extra_arguments_are_rejected(self) -> None:
        for arguments in ({}, {"run_id": "run-1", "extra": "value"}):
            with self.subTest(arguments=arguments):
                with self.assertRaisesRegex(ValueError, "requires exactly"):
                    execute_tool(
                        project_root=self.project_root,
                        tool_name="get_workflow",
                        arguments=arguments,
                    )


if __name__ == "__main__":
    unittest.main()
