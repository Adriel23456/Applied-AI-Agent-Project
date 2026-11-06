"""Utilities for durable, restartable Optuna studies and progress files."""

import hashlib
import json
import os
from pathlib import Path
import sqlite3
from tempfile import NamedTemporaryFile

import optuna


def stable_digest(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def persistent_study(output_dir, database_name, study_name, direction, sampler,
                     manifest, local_storage_dir=None):
    """Open/create one study, optionally working on local SQLite.

    Google Drive is a good place for a durable copy, but a poor filesystem for
    SQLite's small, frequent writes.  When ``local_storage_dir`` is supplied,
    the active database lives there; ``backup_study`` publishes a consistent
    SQLite snapshot to ``output_dir`` at durable milestones.
    """
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    archive_path = directory / database_name
    database_path = archive_path
    if local_storage_dir is not None:
        local_directory = Path(local_storage_dir)
        local_directory.mkdir(parents=True, exist_ok=True)
        database_path = local_directory / database_name
        # A new Colab runtime starts from the last completed Drive snapshot.
        if not database_path.exists() and archive_path.exists():
            _sqlite_backup(archive_path, database_path)
    storage = optuna.storages.RDBStorage(
        url=f"sqlite:///{database_path}",
        engine_kwargs={"connect_args": {"timeout": 60}},
        heartbeat_interval=60,
        grace_period=300,
    )
    study = optuna.create_study(
        study_name=study_name,
        storage=storage,
        direction=direction,
        sampler=sampler,
        load_if_exists=True,
    )
    saved_manifest = study.user_attrs.get("checkpoint_manifest")
    if saved_manifest is None:
        if study.trials:
            raise ValueError(
                f"El estudio {study_name} ya tiene trials pero no un manifiesto. "
                "Usa una carpeta de checkpoints nueva para evitar mezclar corridas."
            )
        study.set_user_attr("checkpoint_manifest", manifest)
    elif saved_manifest != manifest:
        raise ValueError(
            f"La configuración/datos no coinciden con el checkpoint {study_name}. "
            "Restaura la configuración original o usa una carpeta de salida nueva."
        )
    # Private-looking names avoid changing Optuna's public API while keeping
    # the paths available to callbacks that persist every completed fold/trial.
    study._ptcg_active_database = database_path
    study._ptcg_archive_database = archive_path
    return study


def _sqlite_backup(source_path, destination_path):
    """Create a consistent SQLite copy using SQLite's backup API, atomically."""
    source_path, destination_path = Path(source_path), Path(destination_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(suffix=".sqlite3.tmp", dir=destination_path.parent,
                            delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with sqlite3.connect(source_path) as source, sqlite3.connect(temporary_path) as target:
            source.backup(target)
        os.replace(temporary_path, destination_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def backup_study(study):
    """Publish the active local SQLite study to its durable checkpoint, if any."""
    active = getattr(study, "_ptcg_active_database", None)
    archive = getattr(study, "_ptcg_archive_database", None)
    if active is not None and archive is not None and Path(active) != Path(archive):
        _sqlite_backup(active, archive)


def recover_interrupted_trials(study):
    """Requeue interrupted parameter sets so fold checkpoints can finish them.

    Optuna records a killed process as RUNNING forever.  It is explicitly
    marked failed and its exact parameter dictionary is queued again; objective
    functions can then reuse their durable per-fold rows by parameter hash.
    """
    running = [trial for trial in study.get_trials(deepcopy=False)
               if trial.state == optuna.trial.TrialState.RUNNING]
    for trial in running:
        study._storage.set_trial_state_values(
            trial._trial_id, optuna.trial.TrialState.FAIL, None
        )
        if trial.params:
            study.enqueue_trial(trial.params, skip_if_exists=False)
    return len(running)


def complete_trial_rows(study, rows_key="cv_rows"):
    """Recover per-fold records embedded in completed trials."""
    rows = []
    for trial in study.get_trials(deepcopy=False, states=(optuna.trial.TrialState.COMPLETE,)):
        rows.extend(trial.user_attrs.get(rows_key, []))
    return rows


def atomic_csv(records, path):
    """Replace a progress CSV atomically so an interruption cannot truncate it."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", newline="", suffix=".tmp",
                            dir=path.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        import pandas as pd
        pd.DataFrame(records).to_csv(temporary_path, index=False)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def ensure_manifest(path, manifest):
    """Create a checkpoint manifest or reject a mismatched resume attempt."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        saved = json.loads(path.read_text(encoding="utf-8"))
        if saved != manifest:
            raise ValueError(
                f"La configuración/datos no coincide con {path}. "
                "Restaura la configuración original o usa una carpeta nueva."
            )
        return
    with NamedTemporaryFile("w", encoding="utf-8", suffix=".tmp", dir=path.parent,
                            delete=False) as temporary:
        temporary_path = Path(temporary.name)
        json.dump(manifest, temporary, ensure_ascii=False, indent=2, sort_keys=True)
        temporary.write("\n")
    try:
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def atomic_json(value, path):
    """Write a small status/manifest JSON without exposing a partial file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", suffix=".tmp", dir=path.parent,
                            delete=False) as temporary:
        temporary_path = Path(temporary.name)
        json.dump(value, temporary, ensure_ascii=False, indent=2, sort_keys=True)
        temporary.write("\n")
    try:
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def atomic_joblib(value, path):
    """Write a model artifact then atomically publish its final filename."""
    import joblib

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(suffix=".joblib.tmp", dir=path.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        joblib.dump(value, temporary_path)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def json_safe_rows(rows):
    """Convert NumPy/Pandas scalars in metric rows to SQLite JSON values."""
    safe = []
    for row in rows:
        converted = {}
        for key, value in row.items():
            if hasattr(value, "item"):
                value = value.item()
            if value is None or isinstance(value, (str, int, float, bool)):
                converted[key] = value
            else:
                converted[key] = str(value)
        safe.append(converted)
    return safe
