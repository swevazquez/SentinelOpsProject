from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import random
import shutil
from typing import BinaryIO
from urllib.request import urlopen
from zipfile import BadZipFile, ZipFile


DATASET_ID = "NASA-CMAPSS-FD001"
DATASET_LANDING_PAGE = (
    "https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data"
)
ARCHIVE_URL = "https://data.nasa.gov/docs/legacy/CMAPSSData.zip"
ARCHIVE_SHA256 = "74bef434a34db25c7bf72e668ea4cd52afe5f2cf8e44367c55a82bfd91a5a34f"
CONTRACT_VERSION = "1.0.0"
DEFAULT_RUL_CAP = 125
DEFAULT_SPLIT_SEED = 42
DEFAULT_VALIDATION_FRACTION = 0.20

TRAIN_FILENAME = "train_FD001.txt"
TEST_FILENAME = "test_FD001.txt"
TEST_RUL_FILENAME = "RUL_FD001.txt"
README_FILENAME = "readme.txt"
FD001_ARCHIVE_MEMBERS = (
    TRAIN_FILENAME,
    TEST_FILENAME,
    TEST_RUL_FILENAME,
    README_FILENAME,
)

SETTING_FIELDS = tuple(f"setting_{index}" for index in range(1, 4))
SENSOR_FIELDS = tuple(f"sensor_{index}" for index in range(1, 22))
RAW_FIELDS = ("engine_id", "cycle", *SETTING_FIELDS, *SENSOR_FIELDS)
LABELED_FIELDS = (*RAW_FIELDS, "rul_uncapped", "rul")


@dataclass(frozen=True)
class CmapssRecord:
    engine_id: int
    cycle: int
    settings: tuple[float, float, float]
    sensors: tuple[float, ...]

    def as_row(self) -> dict[str, int | float]:
        row: dict[str, int | float] = {
            "engine_id": self.engine_id,
            "cycle": self.cycle,
        }
        row.update(zip(SETTING_FIELDS, self.settings, strict=True))
        row.update(zip(SENSOR_FIELDS, self.sensors, strict=True))
        return row


@dataclass(frozen=True)
class LabeledCmapssRecord:
    record: CmapssRecord
    rul_uncapped: int
    rul: int

    def as_row(self) -> dict[str, int | float]:
        return {
            **self.record.as_row(),
            "rul_uncapped": self.rul_uncapped,
            "rul": self.rul,
        }


@dataclass(frozen=True)
class EngineSplit:
    training_engine_ids: tuple[int, ...]
    validation_engine_ids: tuple[int, ...]


@dataclass(frozen=True)
class PreparationResult:
    training_path: Path
    validation_path: Path
    metadata_path: Path
    training_rows: int
    validation_rows: int


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_download(source: BinaryIO, destination: Path) -> None:
    with destination.open("wb") as output_file:
        shutil.copyfileobj(source, output_file)


def download_archive(
    destination: Path,
    *,
    url: str = ARCHIVE_URL,
    expected_sha256: str = ARCHIVE_SHA256,
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        actual_sha256 = file_sha256(destination)
        if actual_sha256 == expected_sha256:
            return destination
        raise ValueError(
            f"existing C-MAPSS archive checksum mismatch: {actual_sha256}"
        )

    temporary_path = destination.with_suffix(destination.suffix + ".tmp")
    try:
        with urlopen(url, timeout=120) as response:  # nosec B310 - pinned checksum
            _copy_download(response, temporary_path)
        actual_sha256 = file_sha256(temporary_path)
        if actual_sha256 != expected_sha256:
            raise ValueError(
                "downloaded C-MAPSS archive checksum mismatch: "
                f"expected {expected_sha256}, found {actual_sha256}"
            )
        temporary_path.replace(destination)
    finally:
        temporary_path.unlink(missing_ok=True)
    return destination


def extract_fd001(archive_path: Path, output_dir: Path) -> tuple[Path, ...]:
    if file_sha256(archive_path) != ARCHIVE_SHA256:
        raise ValueError("C-MAPSS archive does not match the pinned SHA-256")

    output_dir.mkdir(parents=True, exist_ok=True)
    extracted_paths: list[Path] = []
    try:
        with ZipFile(archive_path) as archive:
            missing = [
                member
                for member in FD001_ARCHIVE_MEMBERS
                if member not in archive.namelist()
            ]
            if missing:
                raise ValueError(
                    "C-MAPSS archive is missing FD001 files: " + ", ".join(missing)
                )

            for member in FD001_ARCHIVE_MEMBERS:
                destination = output_dir / member
                temporary_path = destination.with_suffix(destination.suffix + ".tmp")
                with archive.open(member) as source:
                    _copy_download(source, temporary_path)
                temporary_path.replace(destination)
                extracted_paths.append(destination)
    except BadZipFile as error:
        raise ValueError("C-MAPSS archive is not a valid ZIP file") from error
    return tuple(extracted_paths)


def acquire_fd001(output_dir: Path) -> Path:
    archive_path = output_dir / "CMAPSSData.zip"
    download_archive(archive_path)
    extracted_paths = extract_fd001(archive_path, output_dir)
    metadata = {
        "dataset_id": DATASET_ID,
        "landing_page": DATASET_LANDING_PAGE,
        "archive_url": ARCHIVE_URL,
        "archive_sha256": ARCHIVE_SHA256,
        "files": {
            path.name: {"sha256": file_sha256(path), "bytes": path.stat().st_size}
            for path in extracted_paths
        },
    }
    metadata_path = output_dir / "source-metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata_path


def parse_fd001(path: Path) -> list[CmapssRecord]:
    records: list[CmapssRecord] = []
    observed_keys: set[tuple[int, int]] = set()

    with path.open(encoding="utf-8") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            values = line.split()
            if not values:
                continue
            if len(values) != len(RAW_FIELDS):
                raise ValueError(
                    f"{path}:{line_number} expected {len(RAW_FIELDS)} values, "
                    f"found {len(values)}"
                )

            try:
                numeric_values = [float(value) for value in values]
            except ValueError as error:
                raise ValueError(
                    f"{path}:{line_number} contains a non-numeric value"
                ) from error
            if not all(math.isfinite(value) for value in numeric_values):
                raise ValueError(f"{path}:{line_number} contains a non-finite value")

            engine_value, cycle_value = numeric_values[:2]
            if not engine_value.is_integer() or engine_value < 1:
                raise ValueError(
                    f"{path}:{line_number} engine_id must be a positive integer"
                )
            if not cycle_value.is_integer() or cycle_value < 1:
                raise ValueError(
                    f"{path}:{line_number} cycle must be a positive integer"
                )

            engine_id = int(engine_value)
            cycle = int(cycle_value)
            key = (engine_id, cycle)
            if key in observed_keys:
                raise ValueError(
                    f"{path}:{line_number} duplicates engine {engine_id} cycle {cycle}"
                )
            observed_keys.add(key)
            records.append(
                CmapssRecord(
                    engine_id=engine_id,
                    cycle=cycle,
                    settings=tuple(numeric_values[2:5]),
                    sensors=tuple(numeric_values[5:]),
                )
            )

    if not records:
        raise ValueError(f"{path} must contain at least one C-MAPSS record")

    cycles_by_engine: dict[int, list[int]] = {}
    for record in records:
        cycles_by_engine.setdefault(record.engine_id, []).append(record.cycle)
    for engine_id, cycles in cycles_by_engine.items():
        expected_cycles = list(range(1, max(cycles) + 1))
        if sorted(cycles) != expected_cycles:
            raise ValueError(
                f"engine {engine_id} cycles must be contiguous and begin at 1"
            )

    return sorted(records, key=lambda record: (record.engine_id, record.cycle))


def label_training_records(
    records: list[CmapssRecord],
    *,
    rul_cap: int = DEFAULT_RUL_CAP,
) -> list[LabeledCmapssRecord]:
    if rul_cap < 1:
        raise ValueError("rul_cap must be a positive integer")
    if not records:
        raise ValueError("RUL labeling requires at least one record")

    final_cycles: dict[int, int] = {}
    for record in records:
        final_cycles[record.engine_id] = max(
            final_cycles.get(record.engine_id, 0), record.cycle
        )

    return [
        LabeledCmapssRecord(
            record=record,
            rul_uncapped=final_cycles[record.engine_id] - record.cycle,
            rul=min(final_cycles[record.engine_id] - record.cycle, rul_cap),
        )
        for record in records
    ]


def split_engine_ids(
    records: list[CmapssRecord],
    *,
    validation_fraction: float = DEFAULT_VALIDATION_FRACTION,
    seed: int = DEFAULT_SPLIT_SEED,
) -> EngineSplit:
    if not 0.0 < validation_fraction < 1.0:
        raise ValueError("validation_fraction must be between 0 and 1")

    engine_ids = sorted({record.engine_id for record in records})
    if len(engine_ids) < 2:
        raise ValueError("engine-level splitting requires at least two engines")

    shuffled_ids = engine_ids.copy()
    random.Random(seed).shuffle(shuffled_ids)
    validation_count = max(1, round(len(shuffled_ids) * validation_fraction))
    validation_count = min(validation_count, len(shuffled_ids) - 1)
    validation_ids = tuple(sorted(shuffled_ids[:validation_count]))
    training_ids = tuple(sorted(shuffled_ids[validation_count:]))
    return EngineSplit(
        training_engine_ids=training_ids,
        validation_engine_ids=validation_ids,
    )


def _write_labeled_csv(rows: list[LabeledCmapssRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=LABELED_FIELDS)
        writer.writeheader()
        writer.writerows(row.as_row() for row in rows)
    temporary_path.replace(path)


def prepare_fd001(
    train_path: Path,
    output_dir: Path,
    *,
    rul_cap: int = DEFAULT_RUL_CAP,
    validation_fraction: float = DEFAULT_VALIDATION_FRACTION,
    seed: int = DEFAULT_SPLIT_SEED,
) -> PreparationResult:
    records = parse_fd001(train_path)
    labeled_records = label_training_records(records, rul_cap=rul_cap)
    split = split_engine_ids(
        records,
        validation_fraction=validation_fraction,
        seed=seed,
    )
    training_ids = set(split.training_engine_ids)
    validation_ids = set(split.validation_engine_ids)
    training_rows = [
        row for row in labeled_records if row.record.engine_id in training_ids
    ]
    validation_rows = [
        row for row in labeled_records if row.record.engine_id in validation_ids
    ]

    training_path = output_dir / "training.csv"
    validation_path = output_dir / "validation.csv"
    metadata_path = output_dir / "metadata.json"
    _write_labeled_csv(training_rows, training_path)
    _write_labeled_csv(validation_rows, validation_path)

    metadata = {
        "contract_version": CONTRACT_VERSION,
        "dataset_id": DATASET_ID,
        "source": {
            "landing_page": DATASET_LANDING_PAGE,
            "archive_url": ARCHIVE_URL,
            "archive_sha256": ARCHIVE_SHA256,
            "training_file": train_path.name,
            "training_file_sha256": file_sha256(train_path),
        },
        "schema": {
            "version": CONTRACT_VERSION,
            "raw_fields": list(RAW_FIELDS),
            "labeled_fields": list(LABELED_FIELDS),
            "row_count": len(records),
            "engine_count": len(training_ids | validation_ids),
        },
        "feature_contract": {
            "identifier_fields": ["engine_id", "cycle"],
            "operating_setting_fields": list(SETTING_FIELDS),
            "sensor_fields": list(SENSOR_FIELDS),
            "label_fields": ["rul_uncapped", "rul"],
        },
        "preprocessing_contract": {
            "numeric_policy": "all values must be finite numbers",
            "trajectory_policy": "cycles are contiguous and begin at 1 per engine",
            "record_order": ["engine_id", "cycle"],
            "partition_before_fitting": True,
            "derived_feature_stage": "model training",
        },
        "rul": {
            "formula": "final_cycle_for_engine - current_cycle",
            "cap": rul_cap,
            "target_field": "rul",
            "uncapped_field": "rul_uncapped",
        },
        "split": {
            "method": "engine_id",
            "seed": seed,
            "validation_fraction": validation_fraction,
            "training_engine_ids": list(split.training_engine_ids),
            "validation_engine_ids": list(split.validation_engine_ids),
            "training_rows": len(training_rows),
            "validation_rows": len(validation_rows),
        },
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return PreparationResult(
        training_path=training_path,
        validation_path=validation_path,
        metadata_path=metadata_path,
        training_rows=len(training_rows),
        validation_rows=len(validation_rows),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare NASA C-MAPSS FD001 data.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    acquire_parser = subparsers.add_parser(
        "acquire", help="Download and verify the NASA C-MAPSS archive."
    )
    acquire_parser.add_argument(
        "--output-dir", type=Path, default=Path("data/raw/cmapss")
    )

    prepare_parser = subparsers.add_parser(
        "prepare", help="Label and split an extracted FD001 training file."
    )
    prepare_parser.add_argument(
        "--train-file",
        type=Path,
        default=Path("data/raw/cmapss") / TRAIN_FILENAME,
    )
    prepare_parser.add_argument(
        "--output-dir", type=Path, default=Path("data/processed/cmapss-fd001")
    )
    prepare_parser.add_argument("--rul-cap", type=int, default=DEFAULT_RUL_CAP)
    prepare_parser.add_argument("--seed", type=int, default=DEFAULT_SPLIT_SEED)
    prepare_parser.add_argument(
        "--validation-fraction", type=float, default=DEFAULT_VALIDATION_FRACTION
    )

    args = parser.parse_args()
    if args.command == "acquire":
        metadata_path = acquire_fd001(args.output_dir)
        print(f"Verified FD001 source data: {metadata_path}")
        return

    result = prepare_fd001(
        args.train_file,
        args.output_dir,
        rul_cap=args.rul_cap,
        validation_fraction=args.validation_fraction,
        seed=args.seed,
    )
    print(
        "Prepared FD001 data: "
        f"{result.training_rows} training rows, "
        f"{result.validation_rows} validation rows, "
        f"metadata at {result.metadata_path}"
    )


if __name__ == "__main__":
    main()
