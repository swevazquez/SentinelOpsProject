from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter

from services.ml.prediction_store import CsvPredictionRepository
from services.ml.scoring import score_feature_file
from services.workflows.sprint1 import run_sprint1_workflow
from services.workflows.status import get_workflow_status


DEFAULT_RUNS = 3
DEFAULT_HOURS = 24
DEFAULT_MAX_SECONDS = 5.0
DEFAULT_OUTPUT_DIR = Path("data/performance")


class DemoPerformanceError(RuntimeError):
    pass


@dataclass(frozen=True)
class DemoRunMeasurement:
    run_id: str
    duration_seconds: float
    max_seconds: float
    raw_row_count: int
    feature_row_count: int
    prediction_row_count: int
    workflow_status: str
    passed: bool


@dataclass(frozen=True)
class DemoPerformanceReport:
    runs: int
    hours: int
    max_seconds: float
    passed: bool
    max_duration_seconds: float
    average_duration_seconds: float
    measurements: list[DemoRunMeasurement]


def _round_duration(value: float) -> float:
    return round(value, 4)


def _measure_one_run(
    *,
    project_root: Path,
    run_id: str,
    hours: int,
    max_seconds: float,
    seed: int,
) -> DemoRunMeasurement:
    start = perf_counter()
    workflow_result = run_sprint1_workflow(
        project_root=project_root,
        run_id=run_id,
        hours=hours,
        seed=seed,
    )
    predictions = score_feature_file(workflow_result.feature_path)
    storage_result = CsvPredictionRepository(
        project_root / "data" / "predictions"
    ).save(predictions)
    duration_seconds = _round_duration(perf_counter() - start)
    workflow_status = get_workflow_status(project_root, run_id)
    status_value = workflow_status.status if workflow_status else "missing"

    expected_raw_rows = workflow_result.feature_row_count * hours
    outputs_complete = (
        workflow_result.raw_row_count == expected_raw_rows
        and workflow_result.feature_row_count > 0
        and storage_result.row_count == workflow_result.feature_row_count
        and status_value == "completed"
    )
    passed = outputs_complete and duration_seconds <= max_seconds

    return DemoRunMeasurement(
        run_id=run_id,
        duration_seconds=duration_seconds,
        max_seconds=max_seconds,
        raw_row_count=workflow_result.raw_row_count,
        feature_row_count=workflow_result.feature_row_count,
        prediction_row_count=storage_result.row_count,
        workflow_status=status_value,
        passed=passed,
    )


def run_demo_performance_validation(
    *,
    project_root: Path,
    runs: int = DEFAULT_RUNS,
    hours: int = DEFAULT_HOURS,
    max_seconds: float = DEFAULT_MAX_SECONDS,
    run_prefix: str = "demo-performance",
    seed: int = 42,
) -> DemoPerformanceReport:
    if runs < 1:
        raise ValueError("runs must be at least 1")
    if hours < 1:
        raise ValueError("hours must be at least 1")
    if max_seconds <= 0:
        raise ValueError("max_seconds must be greater than 0")
    if not run_prefix:
        raise ValueError("run_prefix must be non-empty")

    measurements = [
        _measure_one_run(
            project_root=project_root,
            run_id=f"{run_prefix}-{index + 1}",
            hours=hours,
            max_seconds=max_seconds,
            seed=seed + index,
        )
        for index in range(runs)
    ]
    durations = [measurement.duration_seconds for measurement in measurements]
    report = DemoPerformanceReport(
        runs=runs,
        hours=hours,
        max_seconds=max_seconds,
        passed=all(measurement.passed for measurement in measurements),
        max_duration_seconds=max(durations),
        average_duration_seconds=_round_duration(sum(durations) / len(durations)),
        measurements=measurements,
    )
    if not report.passed:
        failed_runs = ", ".join(
            measurement.run_id
            for measurement in report.measurements
            if not measurement.passed
        )
        raise DemoPerformanceError(
            f"demo performance validation failed for runs: {failed_runs}"
        )
    return report


def write_report(report: DemoPerformanceReport, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(asdict(report), indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate demonstration-scale SentinelOps workflow performance."
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--hours", type=int, default=DEFAULT_HOURS)
    parser.add_argument("--max-seconds", type=float, default=DEFAULT_MAX_SECONDS)
    parser.add_argument("--run-prefix", default="demo-performance")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        default=(DEFAULT_OUTPUT_DIR / "latest-demo-performance.json").as_posix(),
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    report = run_demo_performance_validation(
        project_root=project_root,
        runs=args.runs,
        hours=args.hours,
        max_seconds=args.max_seconds,
        run_prefix=args.run_prefix,
        seed=args.seed,
    )
    output_path = write_report(report, project_root / args.output)
    print(
        "Demo performance validation passed: "
        f"{report.runs} runs, max {report.max_duration_seconds:.4f}s, "
        f"average {report.average_duration_seconds:.4f}s, "
        f"threshold {report.max_seconds:.4f}s."
    )
    print(f"Performance report: {output_path.relative_to(project_root)}")


if __name__ == "__main__":
    main()
