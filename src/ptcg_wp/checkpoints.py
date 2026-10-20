"""Utilities for durable, restartable Optuna studies and progress files."""

import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import optuna


def stable_digest(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def persistent_study(output_dir, database_name, study_name, direction, sampler,
                     manifest):
    """Open/create one SQLite-backed study; validate inputs before resuming."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    database_path = directory / database_name
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
    return study


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
