"""Evaluacion comun de TODOS los modelos (B0 a B4 y experimentos): una sola implementacion.

Metricas: AUC, log loss y Brier, globales y por etapa (inicio, medio, final), con el numero
de estados y de partidas de cada grupo. Cada partida pesa lo mismo (peso 1/n por estado, con
n = estados de esa partida dentro del grupo evaluado), asi que una partida larga no domina.

- metric_rows_codes: implementacion unica, sobre codigos enteros de partida y de etapa
  (es la que usan B3, B4, LightGBM, ablaciones y H2 con sus memmaps).
- metric_rows: la misma funcion para ids de partida y etiquetas de etapa en texto
  (B0, B1 y B2 en memoria); convierte a codigos y llama a metric_rows_codes.
- evaluate_stream: ruta por lotes en disco para B2 (mismo resultado, probado en tests).
"""

import numpy as np
import pandas as pd

from ptcg_wp.b2_streaming import evaluate_stream  # noqa: F401  (se reexporta para B2 y B3)

STAGES = ("inicio", "medio", "final")


def metric_rows_codes(y, probability, groups, stage_codes, common, include_stages=True):
    """Metricas ponderadas por partida.

    y: 0/1 por estado. probability: probabilidad de victoria del jugador que actua.
    groups: codigo entero de partida (0..k-1). stage_codes: 0=inicio, 1=medio, 2=final.
    common: columnas fijas que se copian en cada fila (escenario, modelo, ...).
    include_stages=False devuelve solo la fila global (lo usa la validacion cruzada).
    """
    y = np.asarray(y).astype(np.uint8, copy=False)
    probability = np.clip(np.asarray(probability, dtype=float), 1e-15, 1 - 1e-15)
    groups = np.asarray(groups, dtype=np.int64)
    stage_codes = np.asarray(stage_codes)
    if any(len(values) != len(y) for values in (probability, groups)) or (
            include_stages and len(stage_codes) != len(y)):
        raise ValueError("etiquetas, predicciones, partidas y etapas deben tener la misma longitud")
    if not np.isfinite(probability).all():
        raise ValueError("hay probabilidades no finitas")
    grupos = [(None, "global")]
    if include_stages:
        grupos.extend(enumerate(STAGES))
    rows = []
    for code, label in grupos:
        mask = np.ones(len(y), dtype=bool) if code is None else stage_codes == code
        if not mask.any():
            continue
        yy, pp, gg = y[mask], probability[mask], groups[mask]
        # Peso 1/n con n = estados de esa partida dentro de este grupo
        _, inverse, counts = np.unique(gg, return_inverse=True, return_counts=True)
        weights = 1.0 / counts[inverse]
        # AUC ponderado exacto (empates de probabilidad cuentan 1/2), sin aproximar por lotes
        order = np.argsort(pp, kind="mergesort")
        ys, ps, ws = yy[order], pp[order], weights[order]
        starts = np.flatnonzero(np.r_[True, ps[1:] != ps[:-1]])
        positive = np.add.reduceat(ws * ys, starts)
        negative = np.add.reduceat(ws * (1 - ys), starts)
        positives, negatives = positive.sum(), negative.sum()
        favorable = np.sum(positive * (np.r_[0.0, np.cumsum(negative[:-1])] + 0.5 * negative))
        log_loss = -np.sum(weights * (yy * np.log(pp) + (1 - yy) * np.log1p(-pp))) / weights.sum()
        brier = np.sum(weights * (yy - pp) ** 2) / weights.sum()
        rows.append({**common, "etapa": label,
                     "auc": favorable / (positives * negatives) if positives and negatives else np.nan,
                     "log_loss": float(log_loss), "brier": float(brier),
                     "n_estados": int(len(yy)), "n_partidas": int(len(counts))})
    return rows


def metric_rows(y, probability, game_ids, stages, common):
    """Igual que metric_rows_codes, con ids de partida y etapas en texto ("inicio", ...)."""
    game_ids = np.asarray(game_ids)
    stages = np.asarray(stages)
    if len(game_ids) != len(np.asarray(y)) or len(stages) != len(np.asarray(y)):
        raise ValueError("etiquetas, predicciones, partidas y etapas deben tener la misma longitud")
    codigos, _ = pd.factorize(game_ids, sort=True)
    mapa = {stage: code for code, stage in enumerate(STAGES)}
    etapas = np.array([mapa.get(stage, -1) for stage in stages], dtype=np.int8)
    return metric_rows_codes(y, probability, codigos, etapas, common)
