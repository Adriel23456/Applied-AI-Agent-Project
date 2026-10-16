"""B2: regresion logistica regularizada con lectura por dia para Colab."""

import gc

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ptcg_wp.baselines import weights_by_game


# Valores de regularización comparados por búsqueda; C pequeño penaliza más los coeficientes.
C_VALUES = (1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0, 1e3, 1e4)
STAGES = ("inicio", "medio", "final")


def sample_train_games(stream, max_games, seed=2026):
    """Elige partidas completas de train con una semilla reproducible.

    Limitar por partida, en vez de por fila, mantiene juntos los estados de
    cada juego y evita que el ajuste de Colab supere la memoria disponible.
    """
    games = stream._splits.index[stream._splits.eq("train")].to_numpy()
    if max_games is None or len(games) <= max_games:
        return games
    rng = np.random.default_rng(seed)
    return rng.choice(games, size=max_games, replace=False)


def _collect_rows(stream, features, split_name, selected_games=None):
    """Junta un subconjunto de un escenario en arreglos compactos para sklearn.

    Lee los días uno por uno y conserva solo las filas de la partición solicitada
    y, si se indica, de las partidas seleccionadas para un pliegue.
    """
    x_parts, y_parts, game_parts, stage_parts = [], [], [], []
    for day in stream:
        mask = day["split"].eq(split_name)
        if selected_games is not None:
            mask &= day["game_id"].isin(selected_games)
        if not mask.any():
            continue
        part = day.loc[mask]
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
    """Crea el preprocesamiento y clasificador que forman B2.

    El escalador se ajusta junto con la regresión logística dentro de cada
    pliegue, para que no use información de las partidas reservadas.
    """
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


def b2_group_cv(stream, features, c_values=C_VALUES, n_splits=5,
                seed=2026, max_iter=300, max_folds=None, train_games=None):
    """Compara valores de C con GroupKFold, manteniendo juntas las partidas.

    Cada pliegue ajusta con partidas de entrenamiento y mide en partidas
    reservadas. ``max_folds`` permite ejecutar un piloto corto para estimar
    tiempo y memoria antes de lanzar toda la búsqueda.
    """
    if train_games is None:
        train_games = stream._splits.index[stream._splits.eq("train")].to_numpy()
    train_games = np.asarray(train_games)
    splitter = GroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    results = []
    folds = splitter.split(train_games, groups=train_games)

    for fold_number, (fit_idx, held_idx) in enumerate(folds, start=1):
        fit_games = train_games[fit_idx]
        held_games = train_games[held_idx]
        x_fit, y_fit, g_fit, _ = _collect_rows(
            stream, features, "train", selected_games=fit_games
        )
        x_held, y_held, g_held, stage_held = _collect_rows(
            stream, features, "train", selected_games=held_games
        )
        fit_weights = weights_by_game(g_fit)

        for c_value in c_values:
            model = _pipeline(c_value, max_iter)
            model.fit(
                x_fit, y_fit,
                scale__sample_weight=fit_weights,
                logit__sample_weight=fit_weights,
            )
            probability = model.predict_proba(x_held)[:, 1]
            common = {
                "escenario": stream.scenario,
                "C": float(c_value),
                "fold": fold_number,
                "partidas_train_muestra": len(train_games),
                "n_iter": int(model.named_steps["logit"].n_iter_[0]),
                "max_iter_alcanzado": int(model.named_steps["logit"].n_iter_[0]) >= max_iter,
            }
            results.extend(_metric_rows(y_held, probability, g_held, stage_held, common))
            del model, probability

        del x_fit, y_fit, g_fit, x_held, y_held, g_held, stage_held, fit_weights
        gc.collect()
        if max_folds is not None and fold_number >= max_folds:
            break
    return pd.DataFrame(results)


def summarize_b2_cv(fold_results):
    """Promedia resultados de los pliegues y propone hasta tres valores de C.

    Conserva el mejor C según AUC, log loss y Brier, eliminando duplicados.
    """
    global_rows = fold_results.loc[fold_results["etapa"] == "global"]
    summary = global_rows.groupby("C", as_index=False).agg(
        auc=("auc", "mean"),
        auc_sd=("auc", "std"),
        log_loss=("log_loss", "mean"),
        log_loss_sd=("log_loss", "std"),
        brier=("brier", "mean"),
        brier_sd=("brier", "std"),
    )
    ordered = []
    for metric, ascending in (("auc", False), ("log_loss", True), ("brier", True)):
        best = summary.sort_values(metric, ascending=ascending).iloc[0]["C"]
        if best not in ordered:
            ordered.append(float(best))
    summary.insert(0, "escenario", global_rows["escenario"].iloc[0])
    return summary.sort_values("C").reset_index(drop=True), ordered


def fit_b2_candidates_val(stream, features, candidate_cs, max_iter=300,
                          train_games=None):
    """Reajusta finalistas con todo train y los compara en val.

    ``val`` sirve para la decisión final; las particiones ``calib`` y ``test``
    no se leen ni se usan aquí.
    """
    x_fit, y_fit, g_fit, _ = _collect_rows(
        stream, features, "train", selected_games=train_games
    )
    x_val, y_val, g_val, stage_val = _collect_rows(stream, features, "val")
    fit_weights = weights_by_game(g_fit)
    results = []
    for c_value in candidate_cs:
        model = _pipeline(c_value, max_iter)
        model.fit(
            x_fit, y_fit,
            scale__sample_weight=fit_weights,
            logit__sample_weight=fit_weights,
        )
        probability = model.predict_proba(x_val)[:, 1]
        common = {
            "escenario": stream.scenario,
            "modelo": "B2",
            "C": float(c_value),
            "partidas_train_muestra": pd.Series(g_fit).nunique(),
            "n_iter": int(model.named_steps["logit"].n_iter_[0]),
            "max_iter_alcanzado": int(model.named_steps["logit"].n_iter_[0]) >= max_iter,
        }
        results.extend(_metric_rows(y_val, probability, g_val, stage_val, common))
        del model, probability
        gc.collect()
    del x_fit, y_fit, g_fit, x_val, y_val, g_val, stage_val, fit_weights
    gc.collect()
    return pd.DataFrame(results)


def b2_row_split_demo(stream, features, c_value, test_size=0.2,
                      seed=2026, max_iter=300):
    """Demuestra por qué dividir filas puede filtrar partidas entre ambos lados.

    Es un diagnóstico: estados de una misma partida pueden acabar en train y
    evaluación, haciendo que la evaluación parezca más favorable.
    """
    x_all, y_all, games_all, stages_all = _collect_rows(stream, features, "train")
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
