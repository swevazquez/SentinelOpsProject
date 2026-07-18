from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from services.ml.cmapss import (
    DEFAULT_RUL_CAP,
    LABELED_FIELDS,
    CmapssRecord,
    download_archive,
    label_training_records,
    parse_fd001,
    prepare_fd001,
    split_engine_ids,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = PROJECT_ROOT / "tests/fixtures/cmapss/train_FD001_sample.txt"


class _DownloadResponse:
    def __init__(self, content: bytes) -> None:
        self.content = content
        self.offset = 0

    def __enter__(self) -> _DownloadResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = len(self.content) - self.offset
        chunk = self.content[self.offset : self.offset + size]
        self.offset += len(chunk)
        return chunk


def record(engine_id: int, cycle: int) -> CmapssRecord:
    return CmapssRecord(
        engine_id=engine_id,
        cycle=cycle,
        settings=(0.0, 0.0, 100.0),
        sensors=tuple(float(index) for index in range(1, 22)),
    )


class CmapssDataContractTests(unittest.TestCase):
    def test_download_archive_verifies_content_before_persisting(self):
        content = b"pinned C-MAPSS test archive"
        expected_sha256 = hashlib.sha256(content).hexdigest()

        with TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "CMAPSSData.zip"
            with patch(
                "services.ml.cmapss.urlopen",
                return_value=_DownloadResponse(content),
            ):
                result = download_archive(
                    destination,
                    url="https://example.test/CMAPSSData.zip",
                    expected_sha256=expected_sha256,
                )

            self.assertEqual(result.read_bytes(), content)

    def test_download_archive_rejects_checksum_mismatch(self):
        with TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "CMAPSSData.zip"
            with patch(
                "services.ml.cmapss.urlopen",
                return_value=_DownloadResponse(b"unexpected"),
            ):
                with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                    download_archive(
                        destination,
                        url="https://example.test/CMAPSSData.zip",
                        expected_sha256="0" * 64,
                    )

            self.assertFalse(destination.exists())

    def test_parser_maps_the_fd001_schema(self):
        records = parse_fd001(FIXTURE_PATH)

        self.assertEqual(len(records), 9)
        self.assertEqual({item.engine_id for item in records}, {1, 2, 3})
        self.assertEqual(records[0].cycle, 1)
        self.assertEqual(records[0].settings, (-0.0007, -0.0004, 100.0))
        self.assertEqual(len(records[0].sensors), 21)

    def test_parser_rejects_malformed_records(self):
        with TemporaryDirectory() as temp_dir:
            malformed_path = Path(temp_dir) / "malformed.txt"
            malformed_path.write_text("1 1 0.0\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "expected 26 values"):
                parse_fd001(malformed_path)

    def test_parser_rejects_non_numeric_values(self):
        first_row = FIXTURE_PATH.read_text(encoding="utf-8").splitlines()[0]
        with TemporaryDirectory() as temp_dir:
            malformed_path = Path(temp_dir) / "malformed.txt"
            malformed_path.write_text(
                first_row.replace("518.67", "invalid", 1) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "non-numeric value"):
                parse_fd001(malformed_path)

    def test_parser_rejects_incomplete_engine_trajectories(self):
        fixture_rows = FIXTURE_PATH.read_text(encoding="utf-8").splitlines()
        with TemporaryDirectory() as temp_dir:
            malformed_path = Path(temp_dir) / "malformed.txt"
            malformed_path.write_text(
                "\n".join((fixture_rows[0], fixture_rows[2])) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "cycles must be contiguous"):
                parse_fd001(malformed_path)

    def test_rul_labels_use_final_engine_cycle_and_cap_early_life(self):
        records = [record(1, cycle) for cycle in range(1, DEFAULT_RUL_CAP + 3)]

        labeled = label_training_records(records)

        self.assertEqual(labeled[0].rul_uncapped, DEFAULT_RUL_CAP + 1)
        self.assertEqual(labeled[0].rul, DEFAULT_RUL_CAP)
        self.assertEqual(labeled[-1].rul, 0)

    def test_engine_split_is_repeatable_and_has_no_overlap(self):
        records = [record(engine_id, 1) for engine_id in range(1, 11)]

        first = split_engine_ids(records, validation_fraction=0.2, seed=42)
        second = split_engine_ids(records, validation_fraction=0.2, seed=42)

        self.assertEqual(first, second)
        self.assertEqual(len(first.validation_engine_ids), 2)
        self.assertTrue(
            set(first.training_engine_ids).isdisjoint(first.validation_engine_ids)
        )

    def test_prepare_writes_labeled_splits_and_traceability_metadata(self):
        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "processed"

            result = prepare_fd001(
                FIXTURE_PATH,
                output_dir,
                validation_fraction=1 / 3,
                seed=42,
            )

            with result.training_path.open(newline="", encoding="utf-8") as file:
                training_reader = csv.DictReader(file)
                training_rows = list(training_reader)
            with result.validation_path.open(newline="", encoding="utf-8") as file:
                validation_reader = csv.DictReader(file)
                validation_rows = list(validation_reader)
            metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

            training_ids = {row["engine_id"] for row in training_rows}
            validation_ids = {row["engine_id"] for row in validation_rows}
            self.assertEqual(training_reader.fieldnames, list(LABELED_FIELDS))
            self.assertEqual(validation_reader.fieldnames, list(LABELED_FIELDS))
            self.assertTrue(training_ids.isdisjoint(validation_ids))
            self.assertEqual(result.training_rows + result.validation_rows, 9)
            self.assertEqual(metadata["dataset_id"], "NASA-CMAPSS-FD001")
            self.assertEqual(metadata["schema"]["version"], "1.0.0")
            self.assertEqual(
                metadata["feature_contract"]["identifier_fields"],
                ["engine_id", "cycle"],
            )
            self.assertEqual(len(metadata["feature_contract"]["sensor_fields"]), 21)
            self.assertTrue(
                metadata["preprocessing_contract"]["partition_before_fitting"]
            )
            self.assertEqual(metadata["rul"]["cap"], DEFAULT_RUL_CAP)
            self.assertEqual(metadata["split"]["method"], "engine_id")
            self.assertEqual(metadata["split"]["seed"], 42)
            self.assertEqual(len(metadata["source"]["training_file_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
