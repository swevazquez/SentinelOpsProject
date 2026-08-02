from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DependencyRule:
    component_path: Path
    forbidden_prefixes: tuple[str, ...]
    excluded_paths: tuple[Path, ...] = ()


@dataclass(frozen=True)
class DependencyViolation:
    path: Path
    dependency: str

    def __str__(self) -> str:
        return f"{self.path}: forbidden dependency {self.dependency}"


RULES = (
    DependencyRule(
        component_path=Path("services/simulator"),
        forbidden_prefixes=(
            "airflow",
            "services.agent",
            "services.api",
            "services.ml",
            "services.workflows",
        ),
    ),
    DependencyRule(
        component_path=Path("services/spark_jobs"),
        forbidden_prefixes=(
            "airflow",
            "services.agent",
            "services.api",
            "services.ml",
            "services.workflows",
        ),
        excluded_paths=(Path("services/spark_jobs/rul_batch.py"),),
    ),
    DependencyRule(
        component_path=Path("services/spark_jobs/rul_batch.py"),
        forbidden_prefixes=(
            "airflow",
            "services.agent",
            "services.api",
            "services.simulator",
        ),
    ),
    DependencyRule(
        component_path=Path("services/workflows"),
        forbidden_prefixes=(
            "airflow",
            "services.agent",
            "services.api",
            "services.ml",
        ),
    ),
    DependencyRule(
        component_path=Path("airflow/dags"),
        forbidden_prefixes=(
            "services.simulator",
            "services.spark_jobs",
        ),
    ),
)


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def find_dependency_violations(project_root: Path) -> list[DependencyViolation]:
    violations: list[DependencyViolation] = []
    for rule in RULES:
        component_root = project_root / rule.component_path
        paths = (
            [component_root]
            if component_root.is_file()
            else sorted(component_root.rglob("*.py"))
        )
        for path in paths:
            relative_path = path.relative_to(project_root)
            if relative_path in rule.excluded_paths:
                continue
            for dependency in sorted(imported_modules(path)):
                if any(
                    dependency == prefix or dependency.startswith(f"{prefix}.")
                    for prefix in rule.forbidden_prefixes
                ):
                    violations.append(
                        DependencyViolation(
                            path=relative_path,
                            dependency=dependency,
                        )
                    )
    return violations
