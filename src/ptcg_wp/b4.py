"""B4: gradient boosting por histogramas con validación agrupada.

El modelo requiere una matriz completa para cada ajuste. La matriz de cada
escenario se guarda en memmap para que no se duplique al cargar Parquet; cada
modelo materializa únicamente sus grupos de ajuste, vigilancia y evaluación.
"""

from dataclasses import dataclass
from pathlib import Path
import gc
import shutil
import time

import numpy as np
import optuna
import pandas as pd
from sklearn import __version__ as sklearn_version
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

from ptcg_wp.b2_streaming import game_counts
from ptcg_wp.checkpoints import (atomic_csv, atomic_joblib, complete_trial_rows,
                                 ensure_manifest, json_safe_rows, persistent_study,
                                 stable_digest)


METRICS = ("auc", "log_loss", "brier")
STAGES = ("inicio", "medio", "final")
MIN_SKLEARN_EXTERNAL_VAL = (1, 7)


def _version_tuple(version):
    return tuple(int(part) for part in version.split(".")[:2])


def _require_external_validation():
    if _version_tuple(sklearn_version) < MIN_SKLEARN_EXTERNAL_VAL:
        raise RuntimeError(
            "B4 requiere scikit-learn >=1.7 para usar X_val/y_val externos; "
            "instala requirements.txt y reinicia el runtime."
        )


def _check_features(x):
    # HGB maneja NaN de forma nativa, pero infinito casi siempre indica un error.
    if not np.all(np.isfinite(x) | np.isnan(x)):
        raise ValueError("B4 recibió infinito en las características")


def _stage_codes(stages):
    mapping = {stage: code for code, stage in enumerate(STAGES)}
    return np.array([mapping[stage] for stage in stages], dtype=np.int8)


@dataclass
class B4Data:
    """Memmaps de un split y sus grupos, liberados con ``close`` al terminar."""

    directory: Path
    split_name: str
    features: tuple[str, ...]
    games: pd.Index
    n_rows: int

    @property
    def x(self):
        return np.memmap(self.directory / f"{self.split_name}_x.dat", mode="r",
                         dtype=np.float32, shape=(self.n_rows, len(self.features)))

    @property
    def y(self):
        return np.memmap(self.directory / f"{self.split_name}_y.dat", mode="r",
                         dtype=np.uint8, shape=(self.n_rows,))

    @property
    def group(self):
        return np.memmap(self.directory / f"{self.split_name}_group.dat", mode="r",
                         dtype=np.int32, shape=(self.n_rows,))

    @property
    def stage(self):
        return np.memmap(self.directory / f"{self.split_name}_stage.dat", mode="r",
                         dtype=np.int8, shape=(self.n_rows,))

    def close(self):
        # Los objetos memmap se liberan al salir de alcance; GC acelera la liberación
        # antes de que el escenario siguiente reserve su propia matriz.
        gc.collect()


def materialize_split(stream, features, split_name, directory):
    """Escribe un split completo una vez y devuelve índices compactos por partida."""
    directory = Path(directory)
    counts = game_counts(stream, split_name)["global"]
    games = pd.Index(counts.index)
    n_rows = int(counts.sum())
    if not n_rows:
        raise ValueError(f"no hay estados para B4 {split_name}")
    disk_bytes = n_rows * (4 * len(features) + 6)
    if shutil.disk_usage(directory).free < disk_bytes + 512 * 1024**2:
        raise OSError(f"Falta disco para B4 {split_name}: se estiman {disk_bytes / 1024**3:.2f} GiB")
    x = np.memmap(directory / f"{split_name}_x.dat", mode="w+", dtype=np.float32,
                  shape=(n_rows, len(features)))
    y = np.memmap(directory / f"{split_name}_y.dat", mode="w+", dtype=np.uint8, shape=n_rows)
    group = np.memmap(directory / f"{split_name}_group.dat", mode="w+", dtype=np.int32, shape=n_rows)
    stage = np.memmap(directory / f"{split_name}_stage.dat", mode="w+", dtype=np.int8, shape=n_rows)
    game_codes = pd.Series(np.arange(len(games), dtype=np.int32), index=games)
    offset = 0
    for part in stream.iter_batches(split_name, columns=features):
        rows = len(part)
        values = part.loc[:, features].to_numpy(dtype=np.float32, copy=True)
        _check_features(values)
        if not part["y"].isin([0, 1]).all():
            raise ValueError("B4 requiere etiquetas binarias 0/1")
        span = slice(offset, offset + rows)
        x[span], y[span] = values, part["y"].to_numpy(dtype=np.uint8)
        group[span] = part["game_id"].map(game_codes).to_numpy(dtype=np.int32)
        stage[span] = _stage_codes(part["stage"].to_numpy())
        offset += rows
    x.flush(); y.flush(); group.flush(); stage.flush()
    del x, y, group, stage
    if offset != n_rows:
        raise RuntimeError("B4 materializó un número de estados inesperado")
    return B4Data(directory, split_name, tuple(features), games, n_rows)


def _memory_guard(data, max_ram_gib):
    # HGB crea matrices binarias y copias de los grupos. La estimación es
    # deliberadamente conservadora para fallar antes de dejar Colab sin RAM.
    estimated = data.n_rows * len(data.features) * 4 * 4.0
    if estimated > max_ram_gib * 1024**3:
        raise MemoryError(
            f"B4 estima hasta {estimated / 1024**3:.2f} GiB para este escenario; "
            f"el límite configurado es {max_ram_gib:.2f} GiB. "
            "Usa más RAM o reduce el alcance de forma declarada."
        )
    return estimated


def _indices_for_groups(groups, selected):
    return np.flatnonzero(np.isin(groups, selected, assume_unique=False))


def _weights_for_codes(groups):
    counts = np.bincount(groups)
    return 1.0 / counts[groups]


def _metric_rows(y, probability, groups, stage_codes, common):
    probability = np.clip(np.asarray(probability, dtype=float), 1e-15, 1 - 1e-15)
    y = np.asarray(y, dtype=np.uint8)
    rows = []
    for code, label in [(None, "global"), *enumerate(STAGES)]:
        mask = np.ones(len(y), dtype=bool) if code is None else stage_codes == code
        if not mask.any():
            continue
        yy, pp, gg = y[mask], probability[mask], groups[mask]
        weights = _weights_for_codes(gg)
        # AUC ponderado por partida, incluyendo el caso de empates de probabilidad.
        order = np.argsort(pp, kind="mergesort")
        yy, pp, weights = yy[order], pp[order], weights[order]
        positives = np.sum(weights * yy)
        negatives = np.sum(weights * (1 - yy))
        favorable = 0.0
        seen_negative = 0.0
        start = 0
        while start < len(pp):
            end = start + 1
            while end < len(pp) and pp[end] == pp[start]:
                end += 1
            positive = np.sum(weights[start:end] * yy[start:end])
            negative = np.sum(weights[start:end] * (1 - yy[start:end]))
            favorable += positive * (seen_negative + 0.5 * negative)
            seen_negative += negative
            start = end
        logloss = -np.sum(weights * (yy * np.log(pp) + (1 - yy) * np.log1p(-pp))) / weights.sum()
        brier = np.sum(weights * (yy - pp) ** 2) / weights.sum()
        rows.append({**common, "etapa": label,
                     "auc": favorable / (positives * negatives) if positives and negatives else np.nan,
                     "log_loss": logloss, "brier": brier,
                     "n_estados": len(yy), "n_partidas": len(np.unique(gg))})
    return rows


def _parameters(trial):
    # Tasas pequeñas y árboles menos anchos favorecen ajustes graduales; la
    # regularización L2 reduce el efecto de hojas con valores extremos.
    return {
        "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.2, log=True),
        "max_leaf_nodes": trial.suggest_int("max_leaf_nodes", 8, 63, log=True),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 20, 200, log=True),
        "l2_regularization": trial.suggest_float("l2_regularization", 1e-6, 10.0, log=True),
    }


def _make_model(params, seed, max_iter, patience, verbose=0):
    # La pérdida logística conserva probabilidades; la vigilancia externa
    # agrupada decide cuándo parar sin separar filas de una misma partida.
    return HistGradientBoostingClassifier(
        loss="log_loss", max_iter=max_iter, early_stopping=True, scoring="loss",
        n_iter_no_change=patience, tol=1e-7, random_state=seed, verbose=verbose,
        categorical_features=None, **params,
    )


def _fit_with_monitor(data, model_groups, monitor_groups, params, seed,
                      max_iter, patience, verbose=0):
    """Ajusta B4 con dos conjuntos de partidas ya separados.

    Esta función concentra la parte delicada del protocolo: la parada temprana
    ve únicamente el conjunto de vigilancia y nunca las partidas de evaluación
    externa ni ``val``.
    """
    groups = data.group
    model_idx = _indices_for_groups(groups, model_groups)
    monitor_idx = _indices_for_groups(groups, monitor_groups)
    if not len(model_idx) or not len(monitor_idx):
        raise ValueError("B4 necesita partidas tanto para ajuste como para vigilancia")
    x, y = data.x, data.y
    x_model = np.asarray(x[model_idx])
    y_model = np.asarray(y[model_idx])
    g_model = np.asarray(groups[model_idx])
    x_monitor = np.asarray(x[monitor_idx])
    y_monitor = np.asarray(y[monitor_idx])
    g_monitor = np.asarray(groups[monitor_idx])
    model = _make_model(params, seed, max_iter, patience, verbose)
    model.fit(x_model, y_model, sample_weight=_weights_for_codes(g_model),
              X_val=x_monitor, y_val=y_monitor,
              sample_weight_val=_weights_for_codes(g_monitor))
    return model


def _fit_outer_fold(data, fit_groups, held_groups, params, seed, monitor_fraction,
                    max_iter, patience, verbose=0):
    """Ajusta sin tocar el pliegue externo; vigilancia y evaluación son disjuntas."""
    # Primero se reserva un grupo interno para early stopping. El pliegue externo
    # queda intacto y solo produce la métrica de validación cruzada.
    split = GroupShuffleSplit(n_splits=1, test_size=monitor_fraction, random_state=seed)
    inner_idx, monitor_idx = next(split.split(fit_groups, groups=fit_groups))
    model_groups, monitor_groups = fit_groups[inner_idx], fit_groups[monitor_idx]
    groups = data.group
    held_rows = _indices_for_groups(groups, held_groups)
    x_held, y_held = np.asarray(data.x[held_rows]), np.asarray(data.y[held_rows])
    model = _fit_with_monitor(data, model_groups, monitor_groups, params, seed,
                              max_iter, patience, verbose)
    probability = model.predict_proba(x_held)[:, 1]
    held_groups_rows, held_stages = np.asarray(groups[held_rows]), np.asarray(data.stage[held_rows])
    report = _metric_rows(y_held, probability, held_groups_rows, held_stages, {
        "n_iter": model.n_iter_, "partidas_modelo": len(model_groups),
        "partidas_vigilancia": len(monitor_groups), "partidas_evaluacion": len(held_groups),
    })
    return report, model.n_iter_


def b4_optuna_cv(data, n_splits=5, n_trials=10, timeout=None, seed=2026,
                 monitor_fraction=0.15, max_iter=500, patience=30,
                 max_ram_gib=10.0, output_dir=None, verbose=False):
    """Ejecuta un estudio TPE por métrica para evitar ponderaciones arbitrarias."""
    _require_external_validation()
    if not 0 < monitor_fraction < 0.5:
        raise ValueError("monitor_fraction debe estar entre 0 y 0.5")
    if n_trials < 1 or n_splits < 2:
        raise ValueError("n_trials debe ser positivo y n_splits debe ser al menos 2")
    estimated = _memory_guard(data, max_ram_gib)
    all_groups = np.arange(len(data.games), dtype=np.int32)
    folds = list(GroupKFold(n_splits=n_splits, shuffle=True, random_state=seed).split(all_groups, groups=all_groups))
    directions = {"auc": "maximize", "log_loss": "minimize", "brier": "minimize"}
    records, selected = [], []
    output_path = Path(output_dir) if output_dir is not None else None
    progress_path = output_path / "b4_cv_trials.csv" if output_path is not None else None
    for metric_number, metric in enumerate(METRICS):
        sampler = optuna.samplers.TPESampler(seed=seed + metric_number, multivariate=True)
        manifest = {
            "baseline": "B4",
            "features_sha256": stable_digest(list(data.features)),
            "train_games_sha256": stable_digest([str(game) for game in data.games]),
            "n_train_games": int(len(data.games)),
            "n_train_rows": int(data.n_rows),
            "n_splits": int(n_splits),
            "seed": int(seed),
            "monitor_fraction": float(monitor_fraction),
            "max_iter": int(max_iter),
            "patience": int(patience),
            "max_ram_gib": float(max_ram_gib),
            "sklearn_version": sklearn_version,
        }
        if output_path is None:
            study = optuna.create_study(direction=directions[metric], sampler=sampler)
        else:
            study = persistent_study(
                output_path, "b4_optuna.sqlite3", f"b4_{metric}",
                directions[metric], sampler, {**manifest, "metric": metric},
            )

        def objective(trial):
            params = _parameters(trial)
            rows = []
            started = time.perf_counter()
            for fold_number, (fit_idx, held_idx) in enumerate(folds, start=1):
                fold_rows, _ = _fit_outer_fold(data, all_groups[fit_idx], all_groups[held_idx], params,
                                                seed + trial.number * 100 + fold_number,
                                                monitor_fraction, max_iter, patience, int(verbose))
                for row in fold_rows:
                    row.update({"estudio": metric, "trial": trial.number, "fold": fold_number,
                                **params, "tiempo_segundos": time.perf_counter() - started,
                                "memoria_estimada_gib": estimated / 1024**3})
                rows.extend(fold_rows)
            global_rows = [row for row in rows if row["etapa"] == "global"]
            value = float(np.nanmean([row[metric] for row in global_rows]))
            trial.set_user_attr("cv_metrics", {name: float(np.nanmean([row[name] for row in global_rows]))
                                                 for name in METRICS})
            trial.set_user_attr("cv_rows", json_safe_rows(rows))
            return value

        complete_count = sum(
            trial.state == optuna.trial.TrialState.COMPLETE for trial in study.trials
        )
        remaining = max(0, n_trials - complete_count) if output_path is not None else n_trials

        def save_study_progress(current_study, _trial):
            if progress_path is not None:
                atomic_csv(records + complete_trial_rows(current_study), progress_path)

        if remaining:
            study.optimize(objective, n_trials=remaining, timeout=timeout,
                           gc_after_trial=True, show_progress_bar=verbose,
                           callbacks=[save_study_progress] if progress_path is not None else None)
        records.extend(complete_trial_rows(study))
        if progress_path is not None:
            atomic_csv(records, progress_path)
        best = study.best_trial
        selected.append({"seleccionada_por": metric, "trial": best.number,
                         **best.params, **best.user_attrs["cv_metrics"]})
    return pd.DataFrame(records), pd.DataFrame(selected).drop_duplicates(
        subset=["learning_rate", "max_leaf_nodes", "min_samples_leaf", "l2_regularization"]
    ).reset_index(drop=True)


def fit_b4_candidates_val(train_data, val_data, candidates, seed=2026,
                          monitor_fraction=0.15, max_iter=500, patience=30,
                          max_ram_gib=10.0, output_dir=None, scenario=None, verbose=False):
    """Usa vigilancia agrupada para fijar iteraciones y luego compara finalistas en val."""
    _require_external_validation()
    _memory_guard(train_data, max_ram_gib)
    _memory_guard(val_data, max_ram_gib)
    all_groups = np.arange(len(train_data.games), dtype=np.int32)
    split = GroupShuffleSplit(n_splits=1, test_size=monitor_fraction, random_state=seed)
    model_idx, monitor_idx = next(split.split(all_groups, groups=all_groups))
    model_groups, monitor_groups = all_groups[model_idx], all_groups[monitor_idx]
    records = []
    directory = Path(output_dir) if output_dir is not None else None
    progress_path = directory / "b4_val_finalists.csv" if directory is not None else None
    if directory is not None:
        val_manifest = {
            "baseline": "B4_val",
            "scenario": str(scenario),
            "features_sha256": stable_digest(list(train_data.features)),
            "train_games_sha256": stable_digest([str(game) for game in train_data.games]),
            "val_games_sha256": stable_digest([str(game) for game in val_data.games]),
            "candidates_sha256": stable_digest(candidates.to_dict("records")),
            "seed": int(seed),
            "monitor_fraction": float(monitor_fraction),
            "max_iter": int(max_iter),
            "patience": int(patience),
            "max_ram_gib": float(max_ram_gib),
            "sklearn_version": sklearn_version,
        }
        ensure_manifest(directory / "b4_val_manifest.json", val_manifest)
    if progress_path is not None and progress_path.exists():
        records = pd.read_csv(progress_path).to_dict("records")
    completed = {
        (str(row.get("seleccionada_por")), int(row.get("trial", -1)))
        for row in records
    }
    for number, candidate in enumerate(candidates.to_dict("records"), start=1):
        candidate_key = (str(candidate["seleccionada_por"]), int(candidate["trial"]))
        artifact_path = (directory / f"b4_{candidate['seleccionada_por']}_CVtrial{candidate['trial']}.joblib"
                         if directory is not None else None)
        if candidate_key in completed and artifact_path is not None and artifact_path.exists():
            if verbose:
                print(f"B4: finalista {candidate['seleccionada_por']} trial {candidate['trial']} "
                      "ya estaba guardada; se omite", flush=True)
            continue
        records = [row for row in records
                   if (str(row.get("seleccionada_por")), int(row.get("trial", -1))) != candidate_key]
        params = {key: candidate[key] for key in ("learning_rate", "max_leaf_nodes", "min_samples_leaf", "l2_regularization")}
        # Esta primera corrida solo decide n_iter con partidas de vigilancia separadas.
        monitored = _fit_with_monitor(train_data, model_groups, monitor_groups, params,
                                      seed + number, max_iter, patience, int(verbose))
        n_iter = monitored.n_iter_
        train_groups = np.asarray(train_data.group)
        x_train, y_train = np.asarray(train_data.x), np.asarray(train_data.y)
        final = HistGradientBoostingClassifier(loss="log_loss", max_iter=n_iter, early_stopping=False,
                                               random_state=seed + number, categorical_features=None, **params)
        final.fit(x_train, y_train, sample_weight=_weights_for_codes(train_groups))
        probability = final.predict_proba(np.asarray(val_data.x))[:, 1]
        rows = _metric_rows(np.asarray(val_data.y), probability, np.asarray(val_data.group),
                            np.asarray(val_data.stage), {"escenario": scenario, "modelo": "B4", **candidate,
                                                         "n_iter_vigilancia": n_iter,
                                                         "partidas_train": len(train_data.games),
                                                         "partidas_val": len(val_data.games)})
        if directory is not None:
            atomic_joblib({"model": final, "features": list(train_data.features),
                           "n_iter_vigilancia": n_iter, "candidata": candidate,
                           "version_sklearn": sklearn_version},
                          artifact_path)
            records.extend(rows)
            atomic_csv(records, progress_path)
            completed.add(candidate_key)
        else:
            records.extend(rows)
    return pd.DataFrame(records)
