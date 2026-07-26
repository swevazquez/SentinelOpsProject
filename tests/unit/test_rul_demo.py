from __future__ import annotations

import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from services.api.rul_demo import (
    RulDemoBusyError,
    RulDemoCompleteError,
    complete_rul_demo_run,
    current_rul_demo_run_ids,
    release_rul_demo_run,
    reserve_rul_demo_batch,
    reset_rul_demo,
    rul_demo_status,
)
from services.ml.cmapss import RAW_FIELDS, file_sha256
from tests.unit.test_rul_training import write_partition


class RulDemoTests(unittest.TestCase):
    def _prepare_validation(self, root: Path) -> None:
        validation_path = (
            root / "data" / "processed" / "cmapss-fd001" / "validation.csv"
        )
        validation_path.parent.mkdir(parents=True)
        write_partition(validation_path, (5, 6))

    def test_four_checkpoint_demo_is_repeatable_and_retains_history(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._prepare_validation(root)

            first_session = reset_rul_demo(root)["session_id"]
            hashes: list[str] = []
            cycles: list[dict[int, int]] = []
            paths: list[Path] = []
            for checkpoint in range(4):
                batch = reserve_rul_demo_batch(root, f"run-{checkpoint + 1}")
                paths.append(batch.trajectory_path)
                hashes.append(file_sha256(batch.trajectory_path))
                cycles.append(batch.engine_cycles)
                with batch.trajectory_path.open(
                    newline="",
                    encoding="utf-8",
                ) as input_file:
                    reader = csv.DictReader(input_file)
                    self.assertEqual(reader.fieldnames, list(RAW_FIELDS))
                    self.assertTrue(list(reader))
                metadata = json.loads(
                    batch.trajectory_path.with_suffix(".json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertTrue(metadata["labels_excluded"])
                self.assertEqual(metadata["checkpoint"]["number"], checkpoint + 1)
                self.assertEqual(metadata["trajectory"]["sha256"], hashes[-1])
                self.assertEqual(
                    metadata["simulation_mode"],
                    "held_out_trajectory_replay",
                )
                complete_rul_demo_run(root, f"run-{checkpoint + 1}")

            final_status = rul_demo_status(root)
            self.assertEqual(final_status["status"], "complete")
            self.assertEqual(final_status["completed_checkpoints"], 4)
            self.assertTrue(all(path.is_file() for path in paths))
            self.assertTrue(
                all(
                    cycles[index][engine_id] < cycles[index + 1][engine_id]
                    for index in range(3)
                    for engine_id in cycles[index]
                )
            )
            with self.assertRaisesRegex(RulDemoCompleteError, "reset"):
                reserve_rul_demo_batch(root, "run-5")

            reset_status = reset_rul_demo(root)
            self.assertEqual(reset_status["status"], "ready")
            self.assertNotEqual(reset_status["session_id"], first_session)
            replay = reserve_rul_demo_batch(root, "replay-1")
            self.assertEqual(file_sha256(replay.trajectory_path), hashes[0])
            self.assertTrue(all(path.is_file() for path in paths))

    def test_failed_run_releases_checkpoint_for_exact_retry(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._prepare_validation(root)

            first = reserve_rul_demo_batch(root, "failed-run")
            first_hash = file_sha256(first.trajectory_path)
            self.assertEqual(current_rul_demo_run_ids(root), {"failed-run"})
            with self.assertRaisesRegex(RulDemoBusyError, "failed-run"):
                reserve_rul_demo_batch(root, "overlapping-run")
            with self.assertRaisesRegex(RulDemoBusyError, "failed-run"):
                reset_rul_demo(root)
            release_rul_demo_run(root, "failed-run")
            retry = reserve_rul_demo_batch(root, "retry-run")

            self.assertEqual(retry.checkpoint_index, 0)
            self.assertEqual(file_sha256(retry.trajectory_path), first_hash)
            complete_rul_demo_run(root, "retry-run")
            reset_rul_demo(root)
            self.assertEqual(current_rul_demo_run_ids(root), set())


if __name__ == "__main__":
    unittest.main()
