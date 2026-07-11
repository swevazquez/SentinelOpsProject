from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from services.ml.scoring import PREDICTION_FIELDS


DEFAULT_PREDICTION_STORAGE_DIR = Path("data/predictions")


@dataclass(frozen=True)
class PredictionStorageResult:
    path: Path
    run_id: str
    row_count: int


class PredictionRepository(Protocol):
    def save(self, rows: list[dict[str, str]]) -> PredictionStorageResult: ...

    def get_by_run(self, run_id: str) -> list[dict[str, str]]: ...

    def get_by_asset(self, asset_id: str) -> list[dict[str, str]]: ...

    def get_latest(self) -> list[dict[str, str]]: ...


def _validate_identifier(value: str, name: str) -> None:
    if not value or any(character in value for character in ("/", "\\", "..")):
        raise ValueError(f"{name} must be a non-empty file-safe value")


def _validate_prediction_rows(rows: list[dict[str, str]]) -> str:
    if not rows:
        raise ValueError("prediction storage requires at least one row")

    missing_fields = [
        field
        for field in PREDICTION_FIELDS
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
    ]
    if invalid_scores:
        assets = ", ".join(sorted(invalid_scores))
        raise ValueError(f"risk_score must be between 0 and 1 for assets: {assets}")

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
        latest_by_asset: dict[str, dict[str, str]] = {}
        for path in sorted(self.storage_dir.glob("predictions_*.csv")):
            for row in self._read(path):
                current = latest_by_asset.get(row["asset_id"])
                if current is None or row["scored_at"] > current["scored_at"]:
                    latest_by_asset[row["asset_id"]] = row
        return sorted(latest_by_asset.values(), key=lambda row: row["asset_id"])

    @staticmethod
    def _read(path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as input_file:
            reader = csv.DictReader(input_file)
            if reader.fieldnames != PREDICTION_FIELDS:
                raise ValueError(f"prediction file has an invalid schema: {path}")
            return list(reader)
