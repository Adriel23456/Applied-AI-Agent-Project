"""B2: regresión logística L2 con entrenamiento por lotes y todos los juegos."""

import gc
from pathlib import Path
from tempfile import TemporaryDirectory
import warnings

import joblib

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ptcg_wp.baselines import weights_by_game
from ptcg_wp.b2_streaming import (evaluate_stream, fit_incremental, game_counts,
                                 prepare_training)


# Valores de regularización comparados por búsqueda; C pequeño penaliza más los coeficientes.
C_VALUES = (1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0, 1e3, 1e4)
STAGES = ("inicio", "medio", "final")


def sample_train_games(stream, max_games, seed=2026):
    """Elige partidas completas de train con una semilla reproducible.

    Solo para pruebas explícitamente muestreadas; el flujo normal usa todo train.
    """
    games = stream._splits.index[stream._splits.eq("train")].to_numpy()
    if max_games is not None and max_games < 1:
        raise ValueError("max_games debe ser positivo o None")
    if max_games is None or len(games) <= max_games:
        return games
    rng = np.random.default_rng(seed)
    return rng.choice(games, size=max_games, replace=False)


def _collect_rows(stream, features, split_name, selected_games=None, max_rows=100000):
    """Solo para la demo por filas: falla antes de acumular más de max_rows."""
    x_parts, y_parts, game_parts, stage_parts = [], [], [], []
    total = 0
    for part in stream.iter_batches(split_name, selected_games, columns=features):
        total += len(part)
        if total > max_rows:
            raise ValueError("demo por fila demasiado grande; reduce max_games (B2 principal no usa esta demo)")
        x_parts.append(part.loc[:, features].to_numpy(dtype=np.float32))
        y_parts.append(part["y"].to_numpy(dtype=np.uint8))
        game_parts.append(part["game_id"].to_numpy())
        stage_parts.append(part["stage"].to_numpy())
    if not x_parts:
        raise ValueError(f"no hay filas para split={split_name}")
    return (
        np.concatenate(x_parts),
        np.concatenate(y_parts),
        np.concatenate(game_parts),
        np.concatenate(stage_parts),
    )


def _pipeline(c_value, max_iter):
    """LBFGS en memoria, reservado para la demo pequeña de fuga por filas."""
    return Pipeline([
        ("scale", StandardScaler()),
        ("logit", LogisticRegression(
            C=float(c_value), penalty="l2", solver="lbfgs", max_iter=max_iter
        )),
    ])


def _metric_rows(y, probability, game_ids, stages, common):
    """Calcula métricas globales y por etapa, dando igual peso a cada partida."""
    groups = [("global", np.ones(len(y), dtype=bool))]
    groups.extend((stage, stages == stage) for stage in STAGES)
    rows = []
    for stage_name, mask in groups:
        if not mask.any():
            continue
        part_y = y[mask].astype(int, copy=False)
        part_p = np.clip(probability[mask], 1e-15, 1 - 1e-15)
        part_games = game_ids[mask]
        weights = weights_by_game(part_games)
        rows.append({
            **common,
            "etapa": stage_name,
            "auc": roc_auc_score(part_y, part_p, sample_weight=weights),
            "log_loss": log_loss(part_y, part_p, sample_weight=weights, labels=[0, 1]),
            "brier": brier_score_loss(part_y, part_p, sample_weight=weights),
            "n_estados": len(part_y),
            "n_partidas": pd.Series(part_games).nunique(),
        })
    return rows


def _training_games(stream, selected):
    available = game_counts(stream, "train")["global"].index
    games = available if selected is None else pd.Index(selected)
    if games.has_duplicates or not games.isin(available).all():
        raise ValueError("train_games debe contener partidas únicas con estados útiles de train")
    if not len(games):
        raise ValueError("train_games está vacío")
    return games.to_numpy(), len(available)


def _save_progress(results, output_dir, filename):
    if output_dir is not None:
        directory = Path(output_dir)
        directory.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(results).to_csv(directory / filename, index=False)


def b2_group_cv(stream, features, c_values=C_VALUES, n_splits=5,
                seed=2026, max_iter=20, max_folds=None, train_games=None,
                cache_dir=None, output_dir=None, eta0=0.05, tolerance=1e-3,
                verbose=True):
    """Compara C por partidas; max_iter cuenta épocas completas de SGD.

    train_games=None incluye todo train útil. max_folds=1 reduce el trabajo del
    piloto, conservando la cobertura de datos. Cachés temporales en disco local
    se eliminan al terminar cada pliegue, incluso ante una excepción normal.
    """
    train_games, available = _training_games(stream, train_games)
    if max_folds is not None and max_folds < 1:
        raise ValueError("max_folds debe ser positivo o None")
    splitter = GroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    results = []
    folds = splitter.split(train_games, groups=train_games)

    for fold_number, (fit_idx, held_idx) in enumerate(folds, start=1):
        fit_games = train_games[fit_idx]
        held_games = train_games[held_idx]
        if verbose:
            print(f"B2 {stream.scenario}, pliegue {fold_number}/{n_splits}: "
                  f"{len(fit_games)} partidas fit, {len(held_games)} retenidas; preparando disco", flush=True)
        with TemporaryDirectory(prefix="b2-fit-", dir=cache_dir) as directory:
            scaler, paths, n_rows, n_games = prepare_training(stream, features, fit_games, directory)
            for c_value in c_values:
                model, info = fit_incremental(scaler, paths, n_rows, n_games, c_value,
                                             max_iter, seed, eta0, tolerance, verbose)
                common = {"escenario": stream.scenario, "C": float(c_value), "fold": fold_number,
                          "partidas_train_muestra": len(train_games),
                          "partidas_train_disponibles": available,
                          "fraccion_train": len(train_games) / available,
                          "batch_size": stream.batch_size, **info}
                results.extend(evaluate_stream(model, stream, features, "train", held_games,
                                               directory, common))
                _save_progress(results, output_dir, f"b2_cv_{stream.scenario}.csv")
                del model
        if max_folds is not None and fold_number >= max_folds:
            break
    return pd.DataFrame(results)


def summarize_b2_cv(fold_results):
    """Promedia resultados de los pliegues y propone hasta tres valores de C.

    Conserva el mejor C según AUC, log loss y Brier, eliminando duplicados.
    """
    global_rows = fold_results.loc[fold_results["etapa"] == "global"]
    if not global_rows["convergencia"].all():
        warnings.warn("Hay ajustes B2 sin convergencia: la selección es provisional; "
                      "revisar gradiente_train y aumentar épocas antes de conclusiones finales.",
                      RuntimeWarning, stacklevel=2)
    summary = global_rows.groupby("C", as_index=False).agg(
        auc=("auc", "mean"),
        auc_sd=("auc", "std"),
        log_loss=("log_loss", "mean"),
        log_loss_sd=("log_loss", "std"),
        brier=("brier", "mean"),
        brier_sd=("brier", "std"),
        pliegues_convergentes=("convergencia", "sum"),
        pliegues_evaluados=("fold", "count"),
    )
    ordered = []
    for metric, ascending in (("auc", False), ("log_loss", True), ("brier", True)):
        best = summary.sort_values(metric, ascending=ascending).iloc[0]["C"]
        if best not in ordered:
            ordered.append(float(best))
    summary.insert(0, "escenario", global_rows["escenario"].iloc[0])
    return summary.sort_values("C").reset_index(drop=True), ordered


def fit_b2_candidates_val(stream, features, candidate_cs, max_iter=20,
                          train_games=None, seed=2026, cache_dir=None, output_dir=None,
                          eta0=0.05, tolerance=1e-3, verbose=True):
    """Reajusta finalistas con todo train y los compara en val.

    El escalador y la convergencia se calculan con train. Calib/test no se
    utilizan, aunque compartan archivos Parquet con estados de train/val.
    Si output_dir está definido, guarda cada candidata y sus métricas.
    """
    train_games, available = _training_games(stream, train_games)
    results = []
    with TemporaryDirectory(prefix="b2-final-", dir=cache_dir) as directory:
        scaler, paths, n_rows, n_games = prepare_training(stream, features, train_games, directory)
        for c_value in candidate_cs:
            model, info = fit_incremental(scaler, paths, n_rows, n_games, c_value,
                                         max_iter, seed, eta0, tolerance, verbose)
            common = {"escenario": stream.scenario, "modelo": "B2", "C": float(c_value),
                      "partidas_train_muestra": len(train_games),
                      "partidas_train_disponibles": available, "fraccion_train": len(train_games) / available,
                      "batch_size": stream.batch_size, **info}
            results.extend(evaluate_stream(model, stream, features, "val", None, directory, common))
            _save_progress(results, output_dir, f"b2_val_{stream.scenario}.csv")
            if output_dir is not None:
                artifact = {"model": model, "features": list(features), "cuts": stream.cuts, **common}
                joblib.dump(artifact, Path(output_dir) / f"b2_{stream.scenario}_C{c_value:g}.joblib")
            del model
    return pd.DataFrame(results)


def b2_row_split_demo(stream, features, c_value, test_size=0.2,
                      seed=2026, max_iter=300, max_games=200):
    """Demuestra por qué dividir filas puede filtrar partidas entre ambos lados.

    Es un diagnóstico: estados de una misma partida pueden acabar en train y
    evaluación, haciendo que la evaluación parezca más favorable.
    Usa LBFGS en una muestra explícita y como máximo 100,000 estados; no es
    directamente comparable con los reportes completos del nuevo B2 SGD.
    """
    games = sample_train_games(stream, max_games, seed)
    x_all, y_all, games_all, stages_all = _collect_rows(stream, features, "train", games)
    row_ids = np.arange(len(y_all))
    fit_idx, held_idx = train_test_split(
        row_ids, test_size=test_size, random_state=seed, stratify=y_all
    )
    x_fit, y_fit, games_fit = x_all[fit_idx], y_all[fit_idx], games_all[fit_idx]
    x_held, y_held = x_all[held_idx], y_all[held_idx]
    games_held, stages_held = games_all[held_idx], stages_all[held_idx]
    del x_all, y_all, games_all, stages_all, row_ids, fit_idx, held_idx
    gc.collect()

    fit_weights = weights_by_game(games_fit)
    model = _pipeline(c_value, max_iter)
    model.fit(
        x_fit, y_fit,
        scale__sample_weight=fit_weights,
        logit__sample_weight=fit_weights,
    )
    probability = model.predict_proba(x_held)[:, 1]
    rows = _metric_rows(
        y_held, probability, games_held, stages_held,
        {"escenario": stream.scenario, "modelo": "B2_fila", "C": float(c_value)},
    )
    train_games = np.unique(games_fit)
    held_games = np.unique(games_held)
    overlap = np.intersect1d(train_games, held_games)
    contamination = pd.DataFrame([{
        "escenario": stream.scenario,
        "C": float(c_value),
        "partidas_train_fila": len(train_games),
        "partidas_test_fila": len(held_games),
        "partidas_en_ambos_lados": len(overlap),
        "fraccion_test_con_partida_ya_vista": len(overlap) / len(held_games),
    }])
    del x_fit, y_fit, games_fit, x_held, y_held, games_held, stages_held
    del fit_weights, model, probability
    gc.collect()
    return pd.DataFrame(rows), contamination
