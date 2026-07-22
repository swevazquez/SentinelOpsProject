from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from services.agent.actions import (
    APPROVED_ACTIONS,
    action_schemas,
    prepare_action_request,
)


class AgentActionTests(unittest.TestCase):
    def test_approved_actions_have_closed_strict_schemas(self) -> None:
        self.assertEqual([action.name for action in APPROVED_ACTIONS], ["start_workflow"])
        self.assertEqual(
            action_schemas()[0]["parameters"]["properties"]["workflow"]["enum"],
            ["predictive-maintenance"],
        )
        self.assertFalse(
            action_schemas()[0]["parameters"]["additionalProperties"]
        )
        self.assertTrue(action_schemas()[0]["strict"])

    def test_supported_action_produces_immutable_approval_request(self) -> None:
        request = prepare_action_request(
            action_name="start_workflow",
            arguments={"workflow": "predictive-maintenance"},
        )

        self.assertEqual(request.name, "start_workflow")
        self.assertEqual(dict(request.arguments), {"workflow": "predictive-maintenance"})
        self.assertTrue(request.requires_approval)
        self.assertEqual(len(request.fingerprint), 64)
        with self.assertRaises(TypeError):
            request.arguments["workflow"] = "other"  # type: ignore[index]

    def test_same_action_payload_has_stable_fingerprint(self) -> None:
        first = prepare_action_request(
            action_name="start_workflow",
            arguments={"workflow": "predictive-maintenance"},
        )
        second = prepare_action_request(
            action_name="start_workflow",
            arguments={"workflow": "predictive-maintenance"},
        )

        self.assertEqual(first.fingerprint, second.fingerprint)

    def test_unknown_and_direct_mutation_actions_are_rejected_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            before = list(project_root.rglob("*"))

            for action_name in ("delete_predictions", "write_file", "run_shell"):
                with self.subTest(action_name=action_name):
                    with self.assertRaisesRegex(ValueError, "not approved"):
                        prepare_action_request(
                            action_name=action_name,
                            arguments={"path": "data/predictions"},
                        )

            self.assertEqual(list(project_root.rglob("*")), before)

    def test_malformed_or_unsupported_action_arguments_are_rejected(self) -> None:
        scenarios = (
            {},
            {"workflow": "predictive-maintenance", "extra": "value"},
            {"workflow": "unapproved-workflow"},
            {"workflow": 123},
        )
        for arguments in scenarios:
            with self.subTest(arguments=arguments):
                with self.assertRaises(ValueError):
                    prepare_action_request(
                        action_name="start_workflow",
                        arguments=arguments,
                    )

        with self.assertRaisesRegex(ValueError, "arguments must be an object"):
            prepare_action_request(
                action_name="start_workflow",
                arguments="predictive-maintenance",  # type: ignore[arg-type]
            )

        with self.assertRaisesRegex(ValueError, "name must be a string"):
            prepare_action_request(
                action_name=["start_workflow"],  # type: ignore[arg-type]
                arguments={"workflow": "predictive-maintenance"},
            )


if __name__ == "__main__":
    unittest.main()
