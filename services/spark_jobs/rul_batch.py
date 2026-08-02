from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import logging
import math
import os
from pathlib import Path
from typing import Any

from services.ml.cmapss import RAW_FIELDS, file_sha256
from services.ml.prediction_store import prediction_repository
from services.ml.rul_inference import load_rul_artifact, score_rul_rows
from services.ml.rul_training import DEFAULT_MODEL_VERSION, SEMANTIC_VERSION_PATTERN
from services.workflows.status import record_workflow_status


LOGGER = logging.getLogger(__name__)
DEFAULT_SPARK_MASTER = "local[2]"
SPARK_APP_NAME = "sentinelops-rul-batch"


@dataclass(frozen=True)
class SparkRulBatchConfig:
    project_root: Path
    input_path: Path
    run_id: str
    model_version: str = DEFAULT_MODEL_VERSION
    master: str = DEFAULT_SPARK_MASTER
    scored_at: datetime | None = None


@dataclass(frozen=True)
class SparkRulBatchResult:
    run_id: str
    input_row_count: int
    prediction_row_count: int
    asset_count: int
    model_version: str


def _validate_config(config: SparkRulBatchConfig) -> None:
    if not config.run_id or any(
        character in config.run_id for character in ("/", "\\", "..")
    ):
        raise ValueError("run_id must be a non-empty file-safe value")
    if not SEMANTIC_VERSION_PATTERN.fullmatch(config.model_version):
        raise ValueError("model_version must use semantic MAJOR.MINOR.PATCH format")
    if not config.master.strip():
        raise ValueError("Spark master must be non-empty")


def create_local_spark_session(master: str = DEFAULT_SPARK_MASTER) -> Any:
    try:
        from pyspark.sql import SparkSession
    except ImportError as exc:
        raise RuntimeError(
            "PySpark is unavailable; install the project with the spark extra"
        ) from exc

    return (
        SparkSession.builder.master(master)
        .appName(SPARK_APP_NAME)
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.host", "127.0.0.1")
        .getOrCreate()
    )


def prepare_trajectory_rows_with_spark(
    input_path: Path,
    spark_session: Any,
) -> list[dict[str, float | int]]:
    """Use Spark to validate, type, de-duplicate, and order a C-MAPSS batch."""
    if not input_path.is_file():
        raise ValueError(f"C-MAPSS trajectory does not exist: {input_path}")

    from pyspark.sql import functions as spark_functions

    frame = (
        spark_session.read.option("header", True)
        .option("mode", "FAILFAST")
        .csv(str(input_path.resolve()))
    )
    missing_fields = [field for field in RAW_FIELDS if field not in frame.columns]
    if missing_fields:
        raise ValueError(
            "C-MAPSS trajectory is missing required fields: "
            + ", ".join(missing_fields)
        )

    typed = frame.select(
        *[
            spark_functions.col(field).cast("double").alias(field)
            for field in RAW_FIELDS
        ]
    )
    invalid_numeric = None
    for field in RAW_FIELDS:
        column = spark_functions.col(field)
        invalid_field = (
            column.isNull()
            | spark_functions.isnan(column)
            | column.isin(math.inf, -math.inf)
        )
        invalid_numeric = (
            invalid_field
            if invalid_numeric is None
            else invalid_numeric | invalid_field
        )
    assert invalid_numeric is not None
    if typed.filter(invalid_numeric).limit(1).count():
        raise ValueError("C-MAPSS trajectory fields must contain finite numeric values")

    invalid_identifier = (
        (spark_functions.col("engine_id") < 1)
        | (spark_functions.col("cycle") < 1)
        | (spark_functions.col("engine_id") % 1 != 0)
        | (spark_functions.col("cycle") % 1 != 0)
    )
    if typed.filter(invalid_identifier).limit(1).count():
        raise ValueError("engine_id and cycle must be positive integers")

    duplicate = (
        typed.groupBy("engine_id", "cycle")
        .count()
        .filter(spark_functions.col("count") > 1)
        .limit(1)
        .count()
    )
    if duplicate:
        raise ValueError("C-MAPSS trajectory contains a duplicate engine cycle")

    continuity = typed.groupBy("engine_id").agg(
        spark_functions.min("cycle").alias("first_cycle"),
        spark_functions.max("cycle").alias("last_cycle"),
        spark_functions.count("cycle").alias("cycle_count"),
    )
    discontinuous = continuity.filter(
        (spark_functions.col("first_cycle") != 1)
        | (spark_functions.col("last_cycle") != spark_functions.col("cycle_count"))
    )
    if discontinuous.limit(1).count():
        raise ValueError(
            "C-MAPSS trajectory cycles must be contiguous and begin at 1"
        )

    records = typed.orderBy("engine_id", "cycle").collect()
    if not records:
        raise ValueError("C-MAPSS trajectory must contain at least one row")
    return [
        {
            field: (
                int(record[field])
                if field in ("engine_id", "cycle")
                else float(record[field])
            )
            for field in RAW_FIELDS
        }
        for record in records
    ]


def run_spark_rul_batch(
    config: SparkRulBatchConfig,
    *,
    spark_session: Any | None = None,
) -> SparkRulBatchResult:
    """Run the stable Spark-to-RUL-to-persistence application boundary."""
    _validate_config(config)
    project_root = config.project_root.resolve()
    input_path = (
        config.input_path.resolve()
        if config.input_path.is_absolute()
        else (project_root / config.input_path).resolve()
    )
    source_feature_path = (
        config.input_path.as_posix()
        if not config.input_path.is_absolute()
        else input_path.as_posix()
    )
    owns_session = spark_session is None
    session = spark_session
    current_step = "spark_input_preparation"

    try:
        record_workflow_status(
            project_root=project_root,
            run_id=config.run_id,
            status="running",
            step=current_step,
        )
        if session is None:
            session = create_local_spark_session(config.master)
        session.sparkContext.setLogLevel("ERROR")
        rows = prepare_trajectory_rows_with_spark(input_path, session)

        current_step = "spark_rul_inference"
        record_workflow_status(
            project_root=project_root,
            run_id=config.run_id,
            status="running",
            step=current_step,
        )
        artifact = load_rul_artifact(
            project_root
            / "data"
            / "models"
            / "rul-random-forest"
            / config.model_version
        )
        predictions = score_rul_rows(
            rows,
            artifact,
            run_id=config.run_id,
            source_feature_path=source_feature_path,
            source_feature_sha256=file_sha256(input_path),
            scored_at=config.scored_at,
        )

        current_step = "spark_prediction_persistence"
        record_workflow_status(
            project_root=project_root,
            run_id=config.run_id,
            status="running",
            step=current_step,
        )
        storage = prediction_repository(project_root).save(predictions)
        record_workflow_status(
            project_root=project_root,
            run_id=config.run_id,
            status="completed",
        )
        return SparkRulBatchResult(
            run_id=config.run_id,
            input_row_count=len(rows),
            prediction_row_count=storage.row_count,
            asset_count=len({row["asset_id"] for row in predictions}),
            model_version=config.model_version,
        )
    except Exception as exc:
        try:
            record_workflow_status(
                project_root=project_root,
                run_id=config.run_id,
                status="failed",
                step=current_step,
                error=_sanitized_error(exc),
            )
        except Exception:
            LOGGER.exception(
                "unable to persist Spark batch failure run_id=%s",
                config.run_id,
            )
        raise
    finally:
        if owns_session and session is not None:
            session.stop()


def _sanitized_error(error: Exception) -> str:
    message = " ".join(str(error).split())
    if "postgresql://" in message and "@" in message:
        prefix, remainder = message.split("postgresql://", maxsplit=1)
        _, suffix = remainder.split("@", maxsplit=1)
        message = f"{prefix}postgresql://***@{suffix}"
    return f"{type(error).__name__}: {message}"[:500]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run local Spark preparation and versioned SentinelOps RUL scoring."
    )
    parser.add_argument("--input", required=True, help="C-MAPSS-compatible CSV path.")
    parser.add_argument("--run-id", required=True, help="Workflow run identifier.")
    parser.add_argument(
        "--project-root",
        default=".",
        help="SentinelOps repository root.",
    )
    parser.add_argument(
        "--model-version",
        default=DEFAULT_MODEL_VERSION,
        help="Versioned RUL artifact to load.",
    )
    parser.add_argument(
        "--master",
        default=os.getenv("SPARK_MASTER_URL", DEFAULT_SPARK_MASTER),
        help="Spark master URL; local[2] is the supported demonstration default.",
    )
    arguments = parser.parse_args()

    result = run_spark_rul_batch(
        SparkRulBatchConfig(
            project_root=Path(arguments.project_root),
            input_path=Path(arguments.input),
            run_id=arguments.run_id,
            model_version=arguments.model_version,
            master=arguments.master,
        )
    )
    print(
        "Spark RUL batch completed "
        f"run_id={result.run_id} input_rows={result.input_row_count} "
        f"predictions={result.prediction_row_count} assets={result.asset_count}"
    )


if __name__ == "__main__":
    main()
