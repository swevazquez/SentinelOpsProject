from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from services.agent.audit import AgentAuditLogger
from services.agent.tools import execute_tool


class AgentAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temporary_directory.name)
        self.audit_path = self.project_root / "audit" / "events.jsonl"
        self.audit_logger = AgentAuditLogger(self.audit_path)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _events(self) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in self.audit_path.read_text(encoding="utf-8").splitlines()
        ]

    def test_tool_attempts_record_structured_outcomes_with_correlation(self) -> None:
        correlation_id = "request-123"
        execute_tool(
            project_root=self.project_root,
            tool_name="list_workflows",
            arguments={},
            correlation_id=correlation_id,
            audit_logger=self.audit_logger,
        )
        execute_tool(
            project_root=self.project_root,
            tool_name="get_workflow",
            arguments={"run_id": "missing-run"},
            correlation_id=correlation_id,
            audit_logger=self.audit_logger,
        )
        with self.assertRaises(ValueError):
            execute_tool(
                project_root=self.project_root,
                tool_name="get_workflow",
                arguments={"run_id": "missing-run", "secret": "do-not-log"},
                correlation_id=correlation_id,
                audit_logger=self.audit_logger,
            )
        with self.assertRaises(ValueError):
            execute_tool(
                project_root=self.project_root,
                tool_name="delete_predictions",
                arguments={"token": "do-not-log"},
                correlation_id=correlation_id,
                audit_logger=self.audit_logger,
            )

        events = self._events()
        self.assertEqual(len(events), 4)
        self.assertEqual(
            [event["outcome"] for event in events],
            ["succeeded", "not_found", "rejected", "rejected"],
        )
        self.assertTrue(all(event["correlation_id"] == correlation_id for event in events))
        self.assertTrue(all(event["operation_type"] == "tool" for event in events))
        self.assertTrue(all(float(event["duration_ms"]) >= 0 for event in events))
        self.assertTrue(all(event["timestamp"] for event in events))
        self.assertEqual(events[2]["error_category"], "validation_error")
        self.assertNotIn("do-not-log", self.audit_path.read_text(encoding="utf-8"))
        self.assertNotIn("arguments", self.audit_path.read_text(encoding="utf-8"))

    def test_invalid_operation_name_is_not_written_verbatim(self) -> None:
        unsafe_name = "secret value that should not be written"
        with self.assertRaises(ValueError):
            execute_tool(
                project_root=self.project_root,
                tool_name=unsafe_name,
                arguments={},
                audit_logger=self.audit_logger,
            )

        contents = self.audit_path.read_text(encoding="utf-8")
        self.assertNotIn(unsafe_name, contents)
        self.assertEqual(self._events()[0]["operation_name"], "invalid_operation_name")

    def test_invalid_correlation_context_is_not_written_verbatim(self) -> None:
        unsafe_correlation = "secret correlation value"
        execute_tool(
            project_root=self.project_root,
            tool_name="list_workflows",
            arguments={},
            correlation_id=unsafe_correlation,
            audit_logger=self.audit_logger,
        )

        contents = self.audit_path.read_text(encoding="utf-8")
        self.assertNotIn(unsafe_correlation, contents)
        self.assertEqual(self._events()[0]["correlation_id"], "invalid_correlation_id")


if __name__ == "__main__":
    unittest.main()
