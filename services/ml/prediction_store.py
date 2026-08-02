from __future__ import annotations

import csv
from dataclasses import dataclass
import math
from pathlib import Path
from typing import Protocol

from psycopg.types.json import Jsonb

from services.ml.scoring import LEGACY_PREDICTION_FIELDS, PREDICTION_FIELDS
from services.persistence.config import persistence_settings, prediction_storage_dir
from services.persistence.postgres import postgres_connection


DEFAULT_PREDICTION_STORAGE_DIR = Path("data/predictions")
REQUIRED_PREDICTION_FIELDS = (
    "run_id",
    "asset_id",
    "prediction_type",
    "model_name",
    "model_version",
    "scored_at",
    "source_feature_path",
    "source_feature_sha256",
    "risk_score",
    "health_score",
    "asset_status",
    "maintenance_priority",
    "recommended_action",
)


@dataclass(frozen=True)
class PredictionStorageResult:
    path: Path | None
    run_id: str
    row_count: int


class PredictionRepository(Protocol):
    def save(self, rows: list[dict[str, str]]) -> PredictionStorageResult: ...

    def get_by_run(self, run_id: str) -> list[dict[str, str]]: ...

    def get_by_asset(self, asset_id: str) -> list[dict[str, str]]: ...

    def get_latest(self) -> list[dict[str, str]]: ...

    def get_latest_by_type(self, prediction_type: str) -> list[dict[str, str]]: ...


def _validate_identifier(value: str, name: str) -> None:
    if not value or any(character in value for character in ("/", "\\", "..")):
        raise ValueError(f"{name} must be a non-empty file-safe value")


def _validate_prediction_rows(rows: list[dict[str, str]]) -> str:
    if not rows:
        raise ValueError("prediction storage requires at least one row")

    missing_fields = [
        field
        for field in REQUIRED_PREDICTION_FIELDS
        if any(field not in row or row[field] == "" for row in rows)
    ]
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"prediction rows missing required fields: {missing}")

    run_ids = {row["run_id"] for row in rows}
    if len(run_ids) != 1:
        raise ValueError("prediction rows must contain exactly one workflow run_id")

    run_id = next(iter(run_ids))
    _validate_identifier(run_id, "run_id")

    asset_ids = [row["asset_id"] for row in rows]
    if len(asset_ids) != len(set(asset_ids)):
        raise ValueError("prediction rows must contain one row per asset")

    invalid_scores = [
        row["asset_id"]
        for row in rows
        if not 0.0 <= float(row["risk_score"]) <= 1.0
        or not 0.0 <= float(row["health_score"]) <= 1.0
    ]
    if invalid_scores:
        assets = ", ".join(sorted(invalid_scores))
        raise ValueError(
            f"risk_score and health_score must be between 0 and 1 for assets: {assets}"
        )

    invalid_hashes = [
        row["asset_id"]
        for row in rows
        if len(row["source_feature_sha256"]) != 64
        or any(
            character not in "0123456789abcdef"
            for character in row["source_feature_sha256"]
        )
    ]
    if invalid_hashes:
        assets = ", ".join(sorted(invalid_hashes))
        raise ValueError(f"source feature SHA-256 is invalid for assets: {assets}")

    invalid_types = [
        row["asset_id"]
        for row in rows
        if row["prediction_type"] not in ("risk_baseline", "rul")
    ]
    if invalid_types:
        assets = ", ".join(sorted(invalid_types))
        raise ValueError(f"prediction_type is invalid for assets: {assets}")

    for row in rows:
        if row["prediction_type"] != "rul":
            continue
        required_rul_fields = (
            "model_artifact_sha256",
            "dataset_id",
            "feature_contract_version",
            "remaining_useful_life_cycles",
        )
        missing_rul_fields = [
            field for field in required_rul_fields if not row[field]
        ]
        if missing_rul_fields:
            raise ValueError(
                "RUL prediction rows missing required fields: "
                + ", ".join(missing_rul_fields)
            )
        remaining_useful_life = float(row["remaining_useful_life_cycles"])
        if not math.isfinite(remaining_useful_life) or remaining_useful_life < 0:
            raise ValueError(
                "remaining_useful_life_cycles must be finite and nonnegative"
            )
        artifact_hash = row["model_artifact_sha256"]
        if len(artifact_hash) != 64 or any(
            character not in "0123456789abcdef" for character in artifact_hash
        ):
            raise ValueError("model artifact SHA-256 is invalid")

    return run_id


class CsvPredictionRepository:
    def __init__(self, storage_dir: Path = DEFAULT_PREDICTION_STORAGE_DIR) -> None:
        self.storage_dir = storage_dir

    def save(self, rows: list[dict[str, str]]) -> PredictionStorageResult:
        run_id = _validate_prediction_rows(rows)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.storage_dir / f"predictions_{run_id}.csv"
        temporary_path = output_path.with_suffix(".csv.tmp")

        with temporary_path.open("w", newline="", encoding="utf-8") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=PREDICTION_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        temporary_path.replace(output_path)

        return PredictionStorageResult(
            path=output_path,
            run_id=run_id,
            row_count=len(rows),
        )

    def get_by_run(self, run_id: str) -> list[dict[str, str]]:
        _validate_identifier(run_id, "run_id")
        path = self.storage_dir / f"predictions_{run_id}.csv"
        if not path.exists():
            return []
        return self._read(path)

    def get_by_asset(self, asset_id: str) -> list[dict[str, str]]:
        if not asset_id:
            raise ValueError("asset_id must be non-empty")

        predictions = [
            row
            for path in sorted(self.storage_dir.glob("predictions_*.csv"))
            for row in self._read(path)
            if row["asset_id"] == asset_id
        ]
        return sorted(predictions, key=lambda row: row["scored_at"], reverse=True)

    def get_latest(self) -> list[dict[str, str]]:
        return self._get_latest()

    def get_latest_by_type(self, prediction_type: str) -> list[dict[str, str]]:
        if prediction_type not in ("risk_baseline", "rul"):
            raise ValueError("prediction_type is invalid")
        return self._get_latest(prediction_type=prediction_type)

    def _get_latest(
        self,
        *,
        prediction_type: str | None = None,
    ) -> list[dict[str, str]]:
        latest_by_asset: dict[str, dict[str, str]] = {}
        for path in sorted(self.storage_dir.glob("predictions_*.csv")):
            for row in self._read(path):
                if prediction_type is not None and row["prediction_type"] != prediction_type:
                    continue
                current = latest_by_asset.get(row["asset_id"])
                if current is None or row["scored_at"] > current["scored_at"]:
                    latest_by_asset[row["asset_id"]] = row
        return sorted(latest_by_asset.values(), key=lambda row: row["asset_id"])

    @staticmethod
    def _read(path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as input_file:
            reader = csv.DictReader(input_file)
            if reader.fieldnames == PREDICTION_FIELDS:
                return list(reader)
            if reader.fieldnames != LEGACY_PREDICTION_FIELDS:
                raise ValueError(f"prediction file has an invalid schema: {path}")
            return [
                {
                    **row,
                    "prediction_type": "risk_baseline",
                    "model_artifact_sha256": "",
                    "dataset_id": "",
                    "feature_contract_version": "",
                    "remaining_useful_life_cycles": "",
                    "health_score": f"{1.0 - float(row['risk_score']):.4f}",
                }
                for row in reader
            ]


class PostgresPredictionRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def save(self, rows: list[dict[str, str]]) -> PredictionStorageResult:
        run_id = _validate_prediction_rows(rows)
        with postgres_connection(self.database_url) as connection:
            with connection.transaction():
                connection.execute(
                    "DELETE FROM sentinelops_predictions WHERE run_id = %s",
                    (run_id,),
                )
                with connection.cursor() as cursor:
                    cursor.executemany(
                        """
                        INSERT INTO sentinelops_predictions (
                            run_id,
                            asset_id,
                            prediction_type,
                            scored_at,
                            payload
                        ) VALUES (%s, %s, %s, %s, %s)
                        """,
                        [
                            (
                                row["run_id"],
                                row["asset_id"],
                                row["prediction_type"],
                                row["scored_at"],
                                Jsonb(row),
                            )
                            for row in rows
                        ],
                    )
        return PredictionStorageResult(
            path=None,
            run_id=run_id,
            row_count=len(rows),
        )

    def get_by_run(self, run_id: str) -> list[dict[str, str]]:
        _validate_identifier(run_id, "run_id")
        return self._select_payloads(
            """
            SELECT payload
            FROM sentinelops_predictions
            WHERE run_id = %s
            ORDER BY asset_id
            """,
            (run_id,),
        )

    def get_by_asset(self, asset_id: str) -> list[dict[str, str]]:
        if not asset_id:
            raise ValueError("asset_id must be non-empty")
        return self._select_payloads(
            """
            SELECT payload
            FROM sentinelops_predictions
            WHERE asset_id = %s
            ORDER BY scored_at DESC
            """,
            (asset_id,),
        )

    def get_latest(self) -> list[dict[str, str]]:
        return self._get_latest()

    def get_latest_by_type(self, prediction_type: str) -> list[dict[str, str]]:
        if prediction_type not in ("risk_baseline", "rul"):
            raise ValueError("prediction_type is invalid")
        return self._get_latest(prediction_type=prediction_type)

    def _get_latest(
        self,
        *,
        prediction_type: str | None = None,
    ) -> list[dict[str, str]]:
        if prediction_type is None:
            return self._select_payloads(
                """
                SELECT payload
                FROM (
                    SELECT DISTINCT ON (asset_id) asset_id, scored_at, payload
                    FROM sentinelops_predictions
                    ORDER BY asset_id, scored_at DESC
                ) latest
                ORDER BY asset_id
                """
            )
        return self._select_payloads(
            """
            SELECT payload
            FROM (
                SELECT DISTINCT ON (asset_id) asset_id, scored_at, payload
                FROM sentinelops_predictions
                WHERE prediction_type = %s
                ORDER BY asset_id, scored_at DESC
            ) latest
            ORDER BY asset_id
            """,
            (prediction_type,),
        )

    def _select_payloads(
        self,
        query: str,
        parameters: tuple[str, ...] = (),
    ) -> list[dict[str, str]]:
        with postgres_connection(self.database_url) as connection:
            records = connection.execute(query, parameters).fetchall()
        return [dict(record["payload"]) for record in records]


def prediction_repository(project_root: Path) -> PredictionRepository:
    settings = persistence_settings()
    if settings.backend == "postgres":
        assert settings.database_url is not None
        return PostgresPredictionRepository(settings.database_url)
    return CsvPredictionRepository(prediction_storage_dir(project_root))
