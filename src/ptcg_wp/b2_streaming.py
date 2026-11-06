"""Preparación, ajuste y evaluación de B2 con lotes en disco local.

La RAM depende del tamaño del lote y del número de partidas, no de la matriz
completa de estados. Los archivos temporales pertenecen al llamador.
"""

from collections import Counter
from copy import deepcopy
from pathlib import Path
import shutil
import sqlite3
from tempfile import NamedTemporaryFile

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn import __version__ as sklearn_version


STAGES = ("inicio", "medio", "final")


def game_counts(stream, split_name, games=None):
    """Cuenta estados por partida y etapa, incluso si cruzan lotes o archivos."""
    counts = {stage: Counter() for stage in ("global", *STAGES)}
    for part in stream.iter_batches(split_name, games, columns=()):
        counts["global"].update(part["game_id"].value_counts().to_dict())
        for stage in STAGES:
            counts[stage].update(part.loc[part["stage"].eq(stage), "game_id"].value_counts().to_dict())
    if not counts["global"]:
        raise ValueError(f"no hay estados útiles para {split_name}")
    return {stage: pd.Series(values, dtype=np.int64) for stage, values in counts.items()}


def row_weights(part, counts):
    weights = part["game_id"].map(counts).rdiv(1.0).to_numpy(dtype=float)
    if not np.isfinite(weights).all():
        raise ValueError("faltan conteos de partidas para los pesos")
    return weights


def feature_array(part, features):
    x = part.loc[:, features].to_numpy(dtype=np.float64, copy=True)
    if not np.isfinite(x).all():
        raise ValueError("B2 necesita características finitas; revisar los datos antes del ajuste")
    if not part["y"].isin([0, 1]).all():
        raise ValueError("B2 necesita etiquetas binarias 0/1")
    return x


def prepare_training(stream, features, games, directory):
    """Fija el escalador con fit solamente y guarda lotes ya escalados en disco."""
    directory = Path(directory)
    counts = game_counts(stream, "train", games)["global"]
    n_rows, n_games = int(counts.sum()), len(counts)
    # Reserva margen para archivos y evaluación; falla antes de llenar el disco.
    required = int(n_rows * (8 * len(features) + 17) * 1.2)
    if shutil.disk_usage(directory).free < required + 256 * 1024**2:
        raise OSError(f"Falta disco local para B2: caché estimada {required / 1024**3:.2f} GiB")
    scaler = StandardScaler()
    for part in stream.iter_batches("train", games, columns=features):
        scaler.partial_fit(feature_array(part, features), sample_weight=row_weights(part, counts))

    paths = []
    classes = set()
    for number, part in enumerate(stream.iter_batches("train", games, columns=features)):
        x = scaler.transform(feature_array(part, features), copy=False)
        y = part["y"].to_numpy(dtype=np.uint8)
        classes.update(np.unique(y).tolist())
        # Promedio de pesos = 1. Así SGD no recibe gradientes diminutos por estado.
        weights = row_weights(part, counts) * (n_rows / n_games)
        path = directory / f"train-{number:06d}.npz"
        np.savez(path, x=x, y=y, weights=weights)
        paths.append(path)
    if classes != {0, 1}:
        raise ValueError("el entrenamiento de B2 necesita ambas clases")
    return scaler, paths, n_rows, n_games


def training_diagnostics(model, paths, n_rows):
    """Mide objetivo y gradiente en TODO fit; no consulta val ni el pliegue retenido."""
    loss = 0.0
    gradient = np.zeros_like(model.coef_[0])
    intercept_gradient = 0.0
    for path in paths:
        with np.load(path) as batch:
            x, y, weights = batch["x"], batch["y"], batch["weights"]
        scores = model.decision_function(x)
        loss += np.dot(weights, np.logaddexp(0.0, scores) - y * scores)
        residual = weights * (expit(scores) - y)
        gradient += x.T @ residual
        intercept_gradient += residual.sum()
    coefficients = model.coef_[0]
    objective = loss / n_rows + 0.5 * model.alpha * np.dot(coefficients, coefficients)
    gradient = gradient / n_rows + model.alpha * coefficients
    norm = max(float(np.max(np.abs(gradient))), abs(intercept_gradient / n_rows))
    if not np.isfinite([objective, norm]).all():
        raise ValueError("B2 diverge: revisar escala de datos y learning_rate")
    return float(objective), float(norm)


def fit_incremental(scaler, paths, n_rows, n_games, c_value, max_iter=20,
                    seed=2026, eta0=0.05, tolerance=1e-3, verbose=True):
    """Regresión logística L2; una iteración es una pasada completa por fit.

    Con w_i=1/n_game, sklearn LogisticRegression minimiza
    sum(w_i*loss_i)/G + ||coef||²/(2*C*G). Multiplicamos pesos por N/G
    para SGD y usamos alpha=1/(C*G), conservando ese mismo objetivo.
    La solución numérica depende de la convergencia, que se reporta aparte.
    """
    if not np.isfinite(c_value) or c_value <= 0 or max_iter < 1:
        raise ValueError("C y max_iter deben ser positivos")
    if not np.isfinite(eta0) or eta0 <= 0 or not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError("eta0 debe ser positivo y tolerance no negativa")
    alpha = 1.0 / (float(c_value) * n_games)
    model = SGDClassifier(loss="log_loss", penalty="l2", alpha=alpha,
                          learning_rate="invscaling", eta0=min(eta0, 0.05 / alpha),
                          power_t=0.25, average=False, random_state=np.random.RandomState(seed),
                          shuffle=True, early_stopping=False, tol=None)
    rng = np.random.default_rng(seed)
    best_objective = np.inf
    best_model = None
    mean_coef = mean_intercept = None
    converged = False
    for epoch in range(1, max_iter + 1):
        # Aleatoriza los lotes; partial_fit aleatoriza las filas dentro de cada lote.
        for index in rng.permutation(len(paths)):
            with np.load(paths[index]) as batch:
                model.partial_fit(batch["x"], batch["y"], classes=np.array([0, 1]),
                                  sample_weight=batch["weights"])
        # Promedia parámetros al terminar épocas completas. En sklearn 1.6.1,
        # average=True no conserva el intercepto estándar entre partial_fit.
        if mean_coef is None:
            mean_coef, mean_intercept = model.coef_.copy(), model.intercept_.copy()
        else:
            mean_coef += (model.coef_ - mean_coef) / epoch
            mean_intercept += (model.intercept_ - mean_intercept) / epoch
        candidate = deepcopy(model)
        candidate.coef_, candidate.intercept_ = mean_coef.copy(), mean_intercept.copy()
        objective, gradient = training_diagnostics(candidate, paths, n_rows)
        if objective < best_objective:
            best_model = candidate
            best_objective, best_gradient, best_epoch = objective, gradient, epoch
        if verbose:
            print(f"  C={c_value:g}, época {epoch}/{max_iter}: objetivo={objective:.6f}, "
                  f"gradiente={gradient:.3g}", flush=True)
        if best_gradient <= tolerance:
            converged = True
        if converged:
            break
    info = {
        "optimizador": "SGD_log_loss_L2",
        "version_sklearn": sklearn_version,
        "promedio_parametros": "fin_de_epocas",
        "max_epocas": max_iter,
        "alpha": alpha,
        "n_iter": epoch,
        "mejor_epoca": best_epoch,
        "convergencia": bool(converged or best_gradient <= tolerance),
        "max_iter_alcanzado": epoch >= max_iter,
        "objetivo_train": best_objective,
        "gradiente_train": best_gradient,
        "tolerancia_gradiente": tolerance,
        "eta0": model.eta0,
        "semilla": seed,
        "n_estados_fit": n_rows,
        "n_partidas_fit": n_games,
    }
    return Pipeline([("scale", scaler), ("logit", best_model)]), info


def disk_auc(connection, stage):
    """AUC ponderado exacto: orden externo en SQLite, incluyendo empates."""
    weight = "wg" if stage == "global" else "ws"
    where = "" if stage == "global" else "WHERE stage = ?"
    parameters = () if stage == "global" else (stage,)
    query = (f"SELECT p, SUM({weight} * y), SUM({weight} * (1-y)) "
             f"FROM predictions {where} GROUP BY p ORDER BY p")
    positives = negatives = favorable = 0.0
    for _, positive, negative in connection.execute(query, parameters):
        favorable += positive * (negatives + 0.5 * negative)
        positives += positive
        negatives += negative
    return favorable / (positives * negatives) if positives and negatives else np.nan


def evaluate_stream(model, stream, features, split_name, games, directory, common):
    """Evalúa todos los estados; solo guarda predicciones en SQLite temporal.

    AUC se calcula conjuntamente, nunca promediando los AUC de los lotes.
    Los pesos de etapa usan el total de estados de esa partida en esa etapa.
    """
    counts = game_counts(stream, split_name, games)
    n_rows = int(counts["global"].sum())
    if shutil.disk_usage(directory).free < n_rows * 160 + 64 * 1024**2:
        raise OSError("Falta disco local para predicciones y ordenamiento exacto del AUC")
    with NamedTemporaryFile(prefix="predictions-", suffix=".sqlite", dir=directory, delete=False) as file:
        path = Path(file.name)
    connection = sqlite3.connect(path)
    totals = {stage: np.zeros(3) for stage in counts}
    try:
        connection.execute("PRAGMA temp_store=FILE")
        connection.execute("PRAGMA cache_size=-8192")
        connection.execute("PRAGMA mmap_size=0")
        connection.execute("CREATE TABLE predictions(p REAL, y INTEGER, stage TEXT, wg REAL, ws REAL)")
        for part in stream.iter_batches(split_name, games, columns=features):
            y = part["y"].to_numpy(dtype=np.uint8)
            p = model.predict_proba(feature_array(part, features))[:, 1]
            if not np.isfinite(p).all():
                raise ValueError("B2 produjo probabilidades no finitas")
            p = np.clip(p, 1e-15, 1 - 1e-15)
            stages = part["stage"].to_numpy()
            wg = row_weights(part, counts["global"])
            ws = np.empty(len(part))
            loss = -(y * np.log(p) + (1 - y) * np.log1p(-p))
            brier = (y - p)**2
            totals["global"] += (wg.sum(), np.dot(wg, loss), np.dot(wg, brier))
            for stage in STAGES:
                mask = stages == stage
                if mask.any():
                    w = row_weights(part.loc[mask], counts[stage])
                    ws[mask] = w
                    totals[stage] += (w.sum(), np.dot(w, loss[mask]), np.dot(w, brier[mask]))
            connection.executemany("INSERT INTO predictions VALUES (?, ?, ?, ?, ?)",
                                   ((float(p[i]), int(y[i]), str(stages[i]), float(wg[i]), float(ws[i]))
                                    for i in range(len(part))))
            connection.commit()
        rows = []
        for stage, (weight_sum, loss, brier) in totals.items():
            if weight_sum:
                rows.append({**common, "etapa": stage, "auc": disk_auc(connection, stage),
                             "log_loss": loss / weight_sum, "brier": brier / weight_sum,
                             "n_estados": int(counts[stage].sum()), "n_partidas": len(counts[stage])})
        return rows
    finally:
        connection.close()
        # Solo elimina la base temporal creada por esta evaluación.
        path.unlink(missing_ok=True)
