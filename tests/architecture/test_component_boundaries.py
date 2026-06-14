from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tests.architecture.dependency_rules import find_dependency_violations


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ComponentBoundaryTests(unittest.TestCase):
    def test_implemented_components_follow_dependency_rules(self):
        violations = find_dependency_violations(PROJECT_ROOT)

        self.assertEqual(
            violations,
            [],
            "\n".join(str(violation) for violation in violations),
        )

    def test_violation_reports_file_and_forbidden_dependency(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            violating_path = project_root / "services" / "simulator" / "invalid.py"
            violating_path.parent.mkdir(parents=True)
            violating_path.write_text(
                "from services.workflows import sprint1\n",
                encoding="utf-8",
            )

            violations = find_dependency_violations(project_root)

        self.assertEqual(len(violations), 1)
        self.assertEqual(
            str(violations[0]),
            "services/simulator/invalid.py: forbidden dependency services.workflows",
        )


if __name__ == "__main__":
    unittest.main()
