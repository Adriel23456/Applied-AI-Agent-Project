"""B3: árbol de decisión y bosque aleatorio con grupos por partida.

Los árboles de scikit-learn no se ajustan de manera incremental. Por ello B3
materializa en RAM solamente las partidas escogidas, nunca una muestra de filas.
``max_train_games=None`` usa todo train; cualquier límite es una muestra
reproducible y queda registrado en cada resultado.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
import gc

import numpy as np
import optuna
import pandas as pd
from sklearn import __version__ as sklearn_version
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold
from sklearn.tree import DecisionTreeClassifier
from ptcg_wp.checkpoints import (atomic_csv, atomic_joblib, atomic_json, backup_study,
                                 complete_trial_rows, ensure_manifest, json_safe_rows,
                                 persistent_study, recover_interrupted_trials,
                                 stable_digest)

from ptcg_wp.b2_streaming import evaluate_stream, game_counts


MODELS = ("B3_arbol", "B3_bosque")
METRICS = ("auc", "log_loss", "brier")


def select_train_games(stream, max_train_games=None, seed=2026):
    """Elige partidas completas y devuelve también el universo disponible."""
    available = game_counts(stream, "train")["global"].index.to_numpy()
    if max_train_games is not None and max_train_games < 1:
        raise ValueError("max_train_games debe ser positivo o None")
    if max_train_games is None or len(available) <= max_train_games:
        return available, len(available)
    chosen = np.random.default_rng(seed).choice(available, size=max_train_games, replace=False)
    # El orden estable hace reproducibles tanto el materializado como GroupKFold.
    return np.sort(chosen), len(available)


def _memory_estimate_gib(n_rows, n_features):
    # Matriz float32, selección del fit, buffers internos del árbol y margen.
    return n_rows * n_features * 4 * 6.0 / 1024**3


def collect_train_rows(stream, features, games, max_ram_gib=10.0):
    """Preasigna una matriz de las partidas seleccionadas sin concatenar lotes."""
    counts = game_counts(stream, "train", games)["global"]
    games = counts.index.to_numpy()
    n_rows = int(counts.sum())
    estimate = _memory_estimate_gib(n_rows, len(features))
    if estimate > max_ram_gib:
        raise MemoryError(
            f"B3 estima {estimate:.2f} GiB para {len(games):,} partidas; "
            f"el límite es {max_ram_gib:.2f} GiB. Reduce max_train_games "
            "(siempre por partidas completas) o usa más RAM."
        )
    x = np.empty((n_rows, len(features)), dtype=np.float32)
    y = np.empty(n_rows, dtype=np.uint8)
    group = np.empty(n_rows, dtype=np.int32)
    game_codes = pd.Series(np.arange(len(games), dtype=np.int32), index=games)
    offset = 0
    for part in stream.iter_batches("train", games, columns=features):
        n_part = len(part)
        values = part.loc[:, features].to_numpy(dtype=np.float32, copy=True)
        if not np.isfinite(values).all():
            raise ValueError("B3 necesita características numéricas finitas")
        labels = part["y"].to_numpy(dtype=np.uint8)
        if not np.isin(labels, [0, 1]).all():
            raise ValueError("B3 necesita etiquetas binarias 0/1")
        current = slice(offset, offset + n_part)
        x[current], y[current] = values, labels
        group[current] = part["game_id"].map(game_codes).to_numpy(dtype=np.int32)
        offset += n_part
    if offset != n_rows or set(np.unique(y)) != {0, 1}:
        raise ValueError("B3 necesita estados completos y ambas clases en train")
    return x, y, group, counts, estimate


def _model(model_name, seed, params, n_jobs=-1):
    # B3 entrega probabilidades para evaluar también log loss y Brier, no solo
    # la clasificación final. Las semillas hacen reproducible cada ajuste.
    common = dict(random_state=seed, class_weight=None)
    max_depth = params["max_depth"]
    max_depth = None if pd.isna(max_depth) else int(max_depth)
    if model_name == "B3_arbol":
        return DecisionTreeClassifier(criterion=params["criterion"],
                                      max_depth=max_depth,
                                      min_samples_leaf=int(params["min_samples_leaf"]),
                                      ccp_alpha=float(params["ccp_alpha"]), **common)
    if model_name == "B3_bosque":
        # Sin bootstrap de filas: cada árbol respeta los pesos por partida; la
        # diversidad viene de max_features en cada división.
        return RandomForestClassifier(n_estimators=int(params["n_estimators"]),
                                      criterion=params["criterion"],
                                      max_features=params["max_features"],
                                      max_depth=max_depth,
                                      min_samples_leaf=int(params["min_samples_leaf"]),
                                      bootstrap=False, n_jobs=n_jobs, **common)
    raise ValueError(f"modelo B3 desconocido: {model_name}")


def _suggest_params(trial, model_name):
    # Espacio deliberadamente acotado tras el piloto: evita bosques de 250
    # árboles casi sin poda que consumían horas por trial. Sigue explorando
    # complejidad, regularización y diversidad, con controles reproducibles.
    if model_name == "B3_arbol":
        return {
            "criterion": trial.suggest_categorical("criterion", ["gini", "entropy", "log_loss"]),
            "max_depth": trial.suggest_categorical("max_depth", [4, 8, 12]),
            "min_samples_leaf": trial.suggest_categorical("min_samples_leaf", [10, 20, 50]),
            "ccp_alpha": trial.suggest_float("ccp_alpha", 1e-7, 1e-2, log=True),
        }
    return {
        "n_estimators": trial.suggest_categorical("n_estimators", [25, 50, 100]),
        "criterion": trial.suggest_categorical("criterion", ["gini", "entropy", "log_loss"]),
        "max_features": trial.suggest_categorical("max_features", ["sqrt", 0.25, 0.5]),
        "max_depth": trial.suggest_categorical("max_depth", [8, 12]),
        "min_samples_leaf": trial.suggest_categorical("min_samples_leaf", [20, 50, 100]),
    }


def _global_metrics(y, probability, groups, common):
    """Exact game-weighted global metrics without rereading train from Parquet."""
    y = np.asarray(y, dtype=np.uint8)
    probability = np.clip(np.asarray(probability, dtype=float), 1e-15, 1 - 1e-15)
    groups = np.asarray(groups, dtype=np.int32)
    weights = 1.0 / np.bincount(groups)[groups]
    order = np.argsort(probability, kind="mergesort")
    yy, pp, ww = y[order], probability[order], weights[order]
    starts = np.flatnonzero(np.r_[True, pp[1:] != pp[:-1]])
    positive = np.add.reduceat(ww * yy, starts)
    negative = np.add.reduceat(ww * (1 - yy), starts)
    positives, negatives = positive.sum(), negative.sum()
    seen_negative = np.r_[0.0, np.cumsum(negative[:-1])]
    favorable = np.sum(positive * (seen_negative + 0.5 * negative))
    log_loss = -np.sum(ww * (yy * np.log(pp) + (1 - yy) * np.log1p(-pp))) / ww.sum()
    brier = np.sum(ww * (yy - pp) ** 2) / ww.sum()
    return {**common, "etapa": "global",
            "auc": favorable / (positives * negatives) if positives and negatives else np.nan,
            "log_loss": float(log_loss), "brier": float(brier),
            "n_estados": len(yy), "n_partidas": len(np.unique(groups))}


def _fold_checkpoint_path(output_path, scenario, model_name, metric, params):
    key = stable_digest(params)[:16]
    return output_path / "fold_checkpoints" / (
        f"b3_{scenario}_{model_name}_{metric}_{key}.json"
    )


def _load_fold_rows(path, params):
    if not path.exists():
        return []
    import json
    saved = json.loads(path.read_text(encoding="utf-8"))
    return saved.get("rows", []) if saved.get("params_sha256") == stable_digest(params) else []


def _common(stream, model_name, selected_games, available_games, seed, estimate,
            params):
    return {
        "escenario": stream.scenario,
        "modelo": model_name,
        "semilla": seed,
        "partidas_train_muestra": len(selected_games),
        "partidas_train_disponibles": available_games,
        "fraccion_train": len(selected_games) / available_games,
        "muestreo": "todo_train" if len(selected_games) == available_games else "partidas_completas_aleatorias",
        **params,
        "ram_estimada_gib": estimate,
        "version_sklearn": sklearn_version,
    }


def b3_optuna_cv(stream, features, n_splits=5, n_trials=10, max_train_games=None,
                 seed=2026, n_jobs=2, max_ram_gib=10.0, max_folds=None,
                 cache_dir=None, output_dir=None, study_cache_dir=None, verbose=True):
    """Busca hiperparámetros para árbol y bosque con GroupKFold dentro de train.

    Hay un estudio TPE por modelo y métrica para que ninguna métrica se combine
    con pesos arbitrarios. Cada configuración se puntúa con los mismos pliegues.
    """
    if n_splits < 2 or n_trials < 1:
        raise ValueError("n_splits debe ser >=2 y n_trials >=1")
    selected_games, available_games = select_train_games(stream, max_train_games, seed)
    x, y, group, counts, estimate = collect_train_rows(stream, features, selected_games, max_ram_gib)
    selected_games = counts.index.to_numpy()
    splitter = GroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    results, candidates = [], []
    output_path = Path(output_dir) if output_dir is not None else None
    progress_path = (output_path / f"b3_cv_{stream.scenario}.csv"
                     if output_path is not None else None)
    with TemporaryDirectory(prefix="b3-cv-", dir=cache_dir) as directory:
        # Se reutilizan exactamente los mismos pliegues para todas las pruebas,
        # de modo que las diferencias reflejen parámetros y no otra partición.
        folds = list(splitter.split(x, y, group))
        if max_folds is not None:
            if max_folds < 1:
                raise ValueError("max_folds debe ser positivo o None")
            folds = folds[:max_folds]

        for model_name in MODELS:
            for metric in METRICS:
                direction = "maximize" if metric == "auc" else "minimize"
                sampler = optuna.samplers.TPESampler(
                    seed=seed + len(candidates), n_startup_trials=3, multivariate=True
                )
                manifest = {
                    "baseline": "B3",
                    "scenario": str(stream.scenario),
                    "model": model_name,
                    "metric": metric,
                    "features_sha256": stable_digest(list(features)),
                    "train_games_sha256": stable_digest([str(game) for game in selected_games]),
                    "available_games": int(available_games),
                    "n_splits": int(n_splits),
                    "n_folds_run": len(folds),
                    "seed": int(seed),
                    "max_train_games": max_train_games,
                    "n_jobs": int(n_jobs),
                    "max_ram_gib": float(max_ram_gib),
                    "search_policy": "fast_v2_global_metrics_fold_checkpoints",
                    "tpe_startup_trials": 3,
                    "sklearn_version": sklearn_version,
                }
                if output_path is None:
                    study = optuna.create_study(direction=direction, sampler=sampler)
                else:
                    study = persistent_study(
                        output_path, "b3_optuna.sqlite3",
                        f"b3_{stream.scenario}_{model_name}_{metric}",
                        direction, sampler, manifest,
                        local_storage_dir=study_cache_dir,
                    )

                # A resumed sampler must not restart its random stream from
                # the original seed (which can repeat an old configuration).
                completed_before = sum(trial.state == optuna.trial.TrialState.COMPLETE
                                       for trial in study.trials)
                study.sampler = optuna.samplers.TPESampler(
                    seed=seed + len(candidates) + 1009 * completed_before,
                    n_startup_trials=3, multivariate=True,
                )
                recovered = recover_interrupted_trials(study)
                if recovered and verbose:
                    print(f"B3 {stream.scenario} {model_name}/{metric}: "
                          f"se reanudan {recovered} trial(s) interrumpido(s)", flush=True)
                backup_study(study)

                def objective(trial):
                    params = _suggest_params(trial, model_name)
                    # Publish RUNNING + fixed params before the first costly fit.
                    # Thus a Drive checkpoint row can always be matched after a
                    # runtime dies between writing that row and the next backup.
                    if output_path is not None:
                        backup_study(study)
                    checkpoint_path = (_fold_checkpoint_path(output_path, stream.scenario,
                                                            model_name, metric, params)
                                       if output_path is not None else None)
                    trial_rows = (_load_fold_rows(checkpoint_path, params)
                                  if checkpoint_path is not None else [])
                    done_folds = {int(row["fold"]) for row in trial_rows}
                    for fold, (fit_idx, held_idx) in enumerate(folds, start=1):
                        if fold in done_folds:
                            continue
                        fit_games = selected_games[np.unique(group[fit_idx])]
                        held_games = selected_games[np.unique(group[held_idx])]
                        # Cada partida aporta peso total uno aunque tenga más estados.
                        weights = 1.0 / np.bincount(group[fit_idx])[group[fit_idx]]
                        model = _model(model_name, seed + trial.number * 100 + fold,
                                       params, n_jobs)
                        model.fit(x[fit_idx], y[fit_idx], sample_weight=weights)
                        common = _common(stream, model_name, selected_games,
                                         available_games, seed, estimate, params)
                        common.update({"estudio": metric, "trial": trial.number,
                                       "fold": fold, "partidas_fit": len(fit_games),
                                       "partidas_evaluacion": len(held_games)})
                        row = _global_metrics(y[held_idx], model.predict_proba(x[held_idx])[:, 1],
                                              group[held_idx], common)
                        trial_rows.append(row)
                        if checkpoint_path is not None:
                            atomic_json({"params_sha256": stable_digest(params), "params": params,
                                         "rows": json_safe_rows(trial_rows)}, checkpoint_path)
                            # Makes the completed folds visible even if the current trial dies.
                            atomic_csv(results + complete_trial_rows(study) + trial_rows,
                                       progress_path)
                            backup_study(study)
                            if verbose:
                                print(f"B3 {stream.scenario} {model_name}/{metric}, "
                                      f"trial {trial.number}, pliegue {fold}/{len(folds)}: "
                                      "checkpoint guardado", flush=True)
                        del model
                        gc.collect()
                    for row in trial_rows:
                        row["trial"] = trial.number
                    global_rows = [row for row in trial_rows if row["etapa"] == "global"]
                    metric_means = {name: float(np.nanmean([row[name] for row in global_rows]))
                                    for name in METRICS}
                    trial.set_user_attr("metricas_cv", metric_means)
                    trial.set_user_attr("cv_rows", json_safe_rows(trial_rows))
                    return metric_means[metric]

                complete_count = sum(
                    trial.state == optuna.trial.TrialState.COMPLETE for trial in study.trials
                )
                remaining = max(0, n_trials - complete_count) if output_path is not None else n_trials

                def save_study_progress(current_study, _trial):
                    if progress_path is not None:
                        atomic_csv(results + complete_trial_rows(current_study), progress_path)
                    backup_study(current_study)

                if remaining:
                    study.optimize(objective, n_trials=remaining, gc_after_trial=True,
                                   show_progress_bar=verbose,
                                   callbacks=[save_study_progress] if progress_path is not None else None)
                results.extend(complete_trial_rows(study))
                if progress_path is not None:
                    atomic_csv(results, progress_path)
                best = study.best_trial
                candidates.append({"escenario": stream.scenario, "modelo": model_name,
                                   "seleccionada_por": metric, "trial": best.number,
                                   **best.params, **best.user_attrs["metricas_cv"]})
    del x, y, group
    gc.collect()
    return pd.DataFrame(results), _deduplicate_candidates(pd.DataFrame(candidates))


def _deduplicate_candidates(candidates):
    if candidates.empty:
        return candidates
    params = [column for column in candidates.columns
              if column not in {"escenario", "modelo", "seleccionada_por", "trial", *METRICS}]
    return candidates.drop_duplicates(subset=["escenario", "modelo", *params]).reset_index(drop=True)


def fit_b3_candidates_val(stream, features, candidates, max_train_games=None, seed=2026,
               n_jobs=2,
               max_ram_gib=10.0, cache_dir=None, output_dir=None, verbose=True):
    """Reajusta finalistas con train completo y usa val solo para compararlas."""
    selected_games, available_games = select_train_games(stream, max_train_games, seed)
    x, y, group, counts, estimate = collect_train_rows(stream, features, selected_games, max_ram_gib)
    selected_games = counts.index.to_numpy()
    # La ponderación por partida se mantiene idéntica a la usada durante CV.
    weights = 1.0 / np.bincount(group)[group]
    results = []
    destination = Path(output_dir) if output_dir is not None else None
    progress_path = destination / f"b3_val_{stream.scenario}.csv" if destination is not None else None
    if destination is not None:
        val_manifest = {
            "baseline": "B3_val",
            "scenario": str(stream.scenario),
            "features_sha256": stable_digest(list(features)),
            "train_games_sha256": stable_digest([str(game) for game in selected_games]),
            "candidates_sha256": stable_digest(candidates.to_dict("records")),
            "seed": int(seed),
            "max_train_games": max_train_games,
            "n_jobs": int(n_jobs),
            "max_ram_gib": float(max_ram_gib),
            "sklearn_version": sklearn_version,
        }
        ensure_manifest(destination / "b3_val_manifest.json", val_manifest)
    if progress_path is not None and progress_path.exists():
        results = pd.read_csv(progress_path).to_dict("records")
    completed = {
        (str(row.get("modelo")), str(row.get("seleccionada_por")), int(row.get("trial", -1)))
        for row in results
    }
    with TemporaryDirectory(prefix="b3-val-", dir=cache_dir) as directory:
        for offset, candidate in enumerate(candidates.to_dict("records")):
            model_name = candidate["modelo"]
            candidate_key = (str(model_name), str(candidate["seleccionada_por"]), int(candidate["trial"]))
            artifact_path = (destination / f"b3_{stream.scenario}_{model_name}_{candidate['seleccionada_por']}.joblib"
                             if destination is not None else None)
            if candidate_key in completed and artifact_path is not None and artifact_path.exists():
                if verbose:
                    print(f"B3 {stream.scenario}: finalista {model_name}/"
                          f"{candidate['seleccionada_por']} ya estaba guardada; se omite", flush=True)
                continue
            results = [row for row in results
                       if (str(row.get("modelo")), str(row.get("seleccionada_por")),
                           int(row.get("trial", -1))) != candidate_key]
            params = {key: candidate[key] for key in candidate
                      if key not in {"escenario", "modelo", "seleccionada_por", "trial", *METRICS}}
            if verbose:
                print(f"B3 {stream.scenario}: reajustando finalista {model_name} "
                      f"({candidate['seleccionada_por']}) con {len(selected_games)} partidas", flush=True)
            model = _model(model_name, seed + offset, params, n_jobs)
            model.fit(x, y, sample_weight=weights)
            common = _common(stream, model_name, selected_games, available_games, seed,
                             estimate, params)
            common.update({key: candidate[key] for key in ("seleccionada_por", "trial", *METRICS)})
            common["partidas_fit"] = len(selected_games)
            candidate_rows = evaluate_stream(model, stream, features, "val", None, directory, common)
            if destination is not None:
                destination.mkdir(parents=True, exist_ok=True)
                atomic_joblib({"model": model, "features": list(features), "cuts": stream.cuts,
                               **common}, artifact_path)
            results.extend(candidate_rows)
            completed.add(candidate_key)
            if progress_path is not None:
                atomic_csv(results, progress_path)
            del model
            gc.collect()
    del x, y, group
    gc.collect()
    result = pd.DataFrame(results)
    return result
