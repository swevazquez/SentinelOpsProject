from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4

from services.ml.cmapss import DATASET_ID, RAW_FIELDS, file_sha256
from services.ml.rul_inference import load_trajectory_rows
from services.ml.rul_training import DEFAULT_MODEL_VERSION, SEMANTIC_VERSION_PATTERN


SCENARIO_SCHEMA_VERSION = "1.0.0"
DEFAULT_CHECKPOINT_FRACTIONS = (0.40, 0.60, 0.80, 1.00)
DEFAULT_CHECKPOINT_LABELS = (
    "Early operation",
    "Developing degradation",
    "Maintenance approaching",
    "Near end of useful life",
)
SCENARIO_PATH = Path("data/samples/rul_demo_scenario.json")
STATE_PATH = Path("data/demo-state/rul_demo_state.json")
RUNTIME_INPUT_DIR = Path("data/raw/rul-demo")
VALIDATION_PATH = Path("data/processed/cmapss-fd001/validation.csv")
_STATE_LOCK = RLock()


class RulDemoCompleteError(ValueError):
    pass


class RulDemoBusyError(ValueError):
    pass


@dataclass(frozen=True)
class RulDemoScenario:
    scenario_id: str
    engine_ids: tuple[int, ...]
    checkpoint_fractions: tuple[float, ...]
    checkpoint_labels: tuple[str, ...]
    model_version: str


@dataclass(frozen=True)
class RulDemoState:
    session_id: str | None
    next_checkpoint_index: int
    active_run_id: str | None
    updated_at: str | None


@dataclass(frozen=True)
class RulDemoBatch:
    scenario_id: str
    session_id: str
    checkpoint_index: int
    checkpoint_label: str
    trajectory_path: Path
    trajectory_row_count: int
    engine_cycles: dict[int, int]


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _session_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"rul-demo-{timestamp}-{uuid4().hex[:8]}"


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)


def _scenario_from_payload(payload: dict[str, Any]) -> RulDemoScenario:
    if payload.get("schema_version") != SCENARIO_SCHEMA_VERSION:
        raise ValueError("RUL demo scenario schema version is incompatible")
    if payload.get("dataset_id") != DATASET_ID:
        raise ValueError("RUL demo scenario dataset identifier is incompatible")

    scenario_id = payload.get("scenario_id")
    engine_ids = payload.get("engine_ids")
    fractions = payload.get("checkpoint_fractions")
    labels = payload.get("checkpoint_labels")
    model_version = payload.get("model_version")
    if not isinstance(scenario_id, str) or not scenario_id:
        raise ValueError("RUL demo scenario_id must be a non-empty string")
    if (
        not isinstance(engine_ids, list)
        or not engine_ids
        or len(engine_ids) != len(set(engine_ids))
        or any(
            not isinstance(engine_id, int) or engine_id < 1
            for engine_id in engine_ids
        )
    ):
        raise ValueError("RUL demo engine_ids must contain unique positive integers")
    if (
        not isinstance(fractions, list)
        or not fractions
        or any(
            not isinstance(fraction, (int, float))
            or not 0 < float(fraction) <= 1
            for fraction in fractions
        )
        or list(fractions) != sorted(fractions)
        or len(set(float(fraction) for fraction in fractions)) != len(fractions)
    ):
        raise ValueError(
            "RUL demo checkpoint_fractions must be unique ascending values in (0, 1]"
        )
    if (
        not isinstance(labels, list)
        or len(labels) != len(fractions)
        or any(not isinstance(label, str) or not label for label in labels)
    ):
        raise ValueError("RUL demo checkpoint_labels must describe every checkpoint")
    if (
        not isinstance(model_version, str)
        or not SEMANTIC_VERSION_PATTERN.fullmatch(model_version)
    ):
        raise ValueError("RUL demo model_version must use semantic versioning")

    return RulDemoScenario(
        scenario_id=scenario_id,
        engine_ids=tuple(engine_ids),
        checkpoint_fractions=tuple(float(fraction) for fraction in fractions),
        checkpoint_labels=tuple(labels),
        model_version=model_version,
    )


def _derived_scenario(project_root: Path) -> RulDemoScenario:
    rows = load_trajectory_rows(project_root / VALIDATION_PATH)
    engine_ids = tuple(sorted({int(row["engine_id"]) for row in rows})[:4])
    return RulDemoScenario(
        scenario_id="fd001-held-out-engine-lifecycle",
        engine_ids=engine_ids,
        checkpoint_fractions=DEFAULT_CHECKPOINT_FRACTIONS,
        checkpoint_labels=DEFAULT_CHECKPOINT_LABELS,
        model_version=DEFAULT_MODEL_VERSION,
    )


def load_rul_demo_scenario(project_root: Path) -> RulDemoScenario:
    path = project_root / SCENARIO_PATH
    if not path.is_file():
        return _derived_scenario(project_root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise ValueError(f"RUL demo scenario is not valid JSON: {path}") from error
    if not isinstance(payload, dict):
        raise ValueError("RUL demo scenario must be an object")
    return _scenario_from_payload(payload)


def _load_state(project_root: Path) -> RulDemoState:
    path = project_root / STATE_PATH
    if not path.is_file():
        return RulDemoState(None, 0, None, None)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise ValueError(f"RUL demo state is not valid JSON: {path}") from error
    if payload.get("schema_version") != SCENARIO_SCHEMA_VERSION:
        raise ValueError("RUL demo state schema version is incompatible")
    session_id = payload.get("session_id")
    next_checkpoint_index = payload.get("next_checkpoint_index")
    active_run_id = payload.get("active_run_id")
    updated_at = payload.get("updated_at")
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("RUL demo state session_id is invalid")
    if not isinstance(next_checkpoint_index, int) or next_checkpoint_index < 0:
        raise ValueError("RUL demo state checkpoint index is invalid")
    if active_run_id is not None and (
        not isinstance(active_run_id, str) or not active_run_id
    ):
        raise ValueError("RUL demo state active run is invalid")
    if not isinstance(updated_at, str) or not updated_at.endswith("Z"):
        raise ValueError("RUL demo state timestamp is invalid")
    return RulDemoState(
        session_id=session_id,
        next_checkpoint_index=next_checkpoint_index,
        active_run_id=active_run_id,
        updated_at=updated_at,
    )


def _save_state(project_root: Path, state: RulDemoState) -> None:
    _write_json_atomic(
        project_root / STATE_PATH,
        {
            "schema_version": SCENARIO_SCHEMA_VERSION,
            **asdict(state),
        },
    )


def rul_demo_status(project_root: Path) -> dict[str, Any]:
    scenario = load_rul_demo_scenario(project_root)
    state = _load_state(project_root)
    total = len(scenario.checkpoint_fractions)
    completed = min(state.next_checkpoint_index, total)
    if state.active_run_id:
        status = "running"
    elif completed >= total:
        status = "complete"
    elif completed:
        status = "in_progress"
    else:
        status = "ready"
    next_checkpoint = None
    if completed < total:
        next_checkpoint = {
            "number": completed + 1,
            "label": scenario.checkpoint_labels[completed],
        }
    return {
        "scenario_id": scenario.scenario_id,
        "session_id": state.session_id,
        "status": status,
        "completed_checkpoints": completed,
        "total_checkpoints": total,
        "next_checkpoint": next_checkpoint,
        "active_run_id": state.active_run_id,
        "engine_ids": list(scenario.engine_ids),
        "checkpoint_labels": list(scenario.checkpoint_labels),
        "model_version": scenario.model_version,
        "history_retained": True,
    }


def _reset_rul_demo(project_root: Path) -> dict[str, Any]:
    state = _load_state(project_root)
    if state.active_run_id:
        raise RulDemoBusyError(
            f"RUL demo workflow is already running: {state.active_run_id}"
        )
    scenario = load_rul_demo_scenario(project_root)
    _save_state(
        project_root,
        RulDemoState(
            session_id=_session_id(),
            next_checkpoint_index=0,
            active_run_id=None,
            updated_at=_utc_now(),
        ),
    )
    return rul_demo_status(project_root) | {"scenario_id": scenario.scenario_id}


def reset_rul_demo(project_root: Path) -> dict[str, Any]:
    with _STATE_LOCK:
        return _reset_rul_demo(project_root)


def _selected_rows(
    project_root: Path,
    scenario: RulDemoScenario,
    checkpoint_index: int,
) -> tuple[list[dict[str, str]], dict[int, int], dict[int, int]]:
    source_path = project_root / VALIDATION_PATH
    rows = load_trajectory_rows(source_path)
    rows_by_engine: dict[int, list[dict[str, str]]] = {}
    for row in rows:
        engine_id = int(row["engine_id"])
        if engine_id not in scenario.engine_ids:
            continue
        rows_by_engine.setdefault(engine_id, []).append(
            {field: str(row[field]) for field in RAW_FIELDS}
        )
    missing_engines = sorted(set(scenario.engine_ids).difference(rows_by_engine))
    if missing_engines:
        missing = ", ".join(str(engine_id) for engine_id in missing_engines)
        raise ValueError(f"RUL demo engines are missing from validation data: {missing}")

    fraction = scenario.checkpoint_fractions[checkpoint_index]
    selected: list[dict[str, str]] = []
    current_cycles: dict[int, int] = {}
    total_cycles: dict[int, int] = {}
    for engine_id in scenario.engine_ids:
        engine_rows = rows_by_engine[engine_id]
        total_cycle = max(int(float(row["cycle"])) for row in engine_rows)
        current_cycle = max(1, min(total_cycle, round(total_cycle * fraction)))
        total_cycles[engine_id] = total_cycle
        current_cycles[engine_id] = current_cycle
        selected.extend(
            row for row in engine_rows if int(float(row["cycle"])) <= current_cycle
        )
    return selected, current_cycles, total_cycles


def _reserve_rul_demo_batch(project_root: Path, run_id: str) -> RulDemoBatch:
    scenario = load_rul_demo_scenario(project_root)
    state = _load_state(project_root)
    if state.active_run_id:
        raise RulDemoBusyError(
            f"RUL demo workflow is already running: {state.active_run_id}"
        )
    if state.next_checkpoint_index >= len(scenario.checkpoint_fractions):
        raise RulDemoCompleteError(
            "RUL demo scenario is complete; reset it before starting another run"
        )

    session_id = state.session_id or _session_id()
    reserved_state = RulDemoState(
        session_id=session_id,
        next_checkpoint_index=state.next_checkpoint_index,
        active_run_id=run_id,
        updated_at=_utc_now(),
    )
    _save_state(project_root, reserved_state)
    try:
        rows, current_cycles, total_cycles = _selected_rows(
            project_root,
            scenario,
            state.next_checkpoint_index,
        )
        output_path = (
            project_root / RUNTIME_INPUT_DIR / f"trajectory_{run_id}.csv"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = output_path.with_suffix(".csv.tmp")
        with temporary_path.open("w", newline="", encoding="utf-8") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=RAW_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        temporary_path.replace(output_path)
        _write_json_atomic(
            output_path.with_suffix(".json"),
            {
                "schema_version": SCENARIO_SCHEMA_VERSION,
                "scenario_id": scenario.scenario_id,
                "session_id": session_id,
                "run_id": run_id,
                "model_version": scenario.model_version,
                "simulation_mode": "held_out_trajectory_replay",
                "checkpoint": {
                    "number": state.next_checkpoint_index + 1,
                    "label": scenario.checkpoint_labels[
                        state.next_checkpoint_index
                    ],
                    "fraction": scenario.checkpoint_fractions[
                        state.next_checkpoint_index
                    ],
                },
                "engine_cycles": {
                    str(engine_id): {
                        "current_cycle": current_cycles[engine_id],
                        "total_cycles": total_cycles[engine_id],
                    }
                    for engine_id in scenario.engine_ids
                },
                "source": {
                    "path": VALIDATION_PATH.as_posix(),
                    "sha256": file_sha256(project_root / VALIDATION_PATH),
                },
                "trajectory": {
                    "path": output_path.relative_to(project_root).as_posix(),
                    "sha256": file_sha256(output_path),
                    "row_count": len(rows),
                },
                "labels_excluded": True,
            },
        )
    except Exception:
        release_rul_demo_run(project_root, run_id)
        raise

    return RulDemoBatch(
        scenario_id=scenario.scenario_id,
        session_id=session_id,
        checkpoint_index=state.next_checkpoint_index,
        checkpoint_label=scenario.checkpoint_labels[state.next_checkpoint_index],
        trajectory_path=output_path,
        trajectory_row_count=len(rows),
        engine_cycles=current_cycles,
    )


def reserve_rul_demo_batch(project_root: Path, run_id: str) -> RulDemoBatch:
    with _STATE_LOCK:
        return _reserve_rul_demo_batch(project_root, run_id)


def _complete_rul_demo_run(project_root: Path, run_id: str) -> dict[str, Any]:
    scenario = load_rul_demo_scenario(project_root)
    state = _load_state(project_root)
    if state.active_run_id != run_id:
        raise ValueError("RUL demo active run does not match workflow completion")
    _save_state(
        project_root,
        RulDemoState(
            session_id=state.session_id,
            next_checkpoint_index=min(
                state.next_checkpoint_index + 1,
                len(scenario.checkpoint_fractions),
            ),
            active_run_id=None,
            updated_at=_utc_now(),
        ),
    )
    return rul_demo_status(project_root)


def complete_rul_demo_run(project_root: Path, run_id: str) -> dict[str, Any]:
    with _STATE_LOCK:
        return _complete_rul_demo_run(project_root, run_id)


def _release_rul_demo_run(project_root: Path, run_id: str) -> None:
    state = _load_state(project_root)
    if state.active_run_id != run_id:
        return
    _save_state(
        project_root,
        RulDemoState(
            session_id=state.session_id,
            next_checkpoint_index=state.next_checkpoint_index,
            active_run_id=None,
            updated_at=_utc_now(),
        ),
    )


def release_rul_demo_run(project_root: Path, run_id: str) -> None:
    with _STATE_LOCK:
        _release_rul_demo_run(project_root, run_id)


def configured_rul_demo_asset_ids(project_root: Path) -> set[str]:
    scenario = load_rul_demo_scenario(project_root)
    return {
        f"FD001-ENGINE-{engine_id:03d}"
        for engine_id in scenario.engine_ids
    }


def current_rul_demo_run_ids(project_root: Path) -> set[str]:
    state = _load_state(project_root)
    if state.session_id is None:
        return set()

    run_ids: set[str] = set()
    metadata_dir = project_root / RUNTIME_INPUT_DIR
    for path in sorted(metadata_dir.glob("trajectory_*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            raise ValueError(f"RUL demo input metadata is not valid: {path}") from error
        if payload.get("session_id") != state.session_id:
            continue
        run_id = payload.get("run_id")
        if (
            not isinstance(run_id, str)
            or not run_id
            or any(character in run_id for character in ("/", "\\", ".."))
        ):
            raise ValueError(f"RUL demo input metadata has an invalid run_id: {path}")
        run_ids.add(run_id)
    return run_ids
