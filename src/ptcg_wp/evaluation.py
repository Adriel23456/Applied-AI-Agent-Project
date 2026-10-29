"""Evaluación común por partida para los baselines de desarrollo.

``metric_rows`` recibe predicciones en memoria. ``evaluate_stream`` ofrece el
mismo informe usando disco para evaluar modelos grandes por lotes.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

from ptcg_wp.baselines import weights_by_game
from ptcg_wp.b2_streaming import evaluate_stream


STAGES = ("inicio", "medio", "final")


def metric_rows(y, probability, game_ids, stages, common):
    """AUC, log loss y Brier globales y por etapa con igual peso por partida."""
    y = np.asarray(y)
    probability = np.asarray(probability)
    game_ids = np.asarray(game_ids)
    stages = np.asarray(stages)
    if any(len(values) != len(y) for values in (probability, game_ids, stages)):
        raise ValueError("etiquetas, predicciones, partidas y etapas deben tener la misma longitud")
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
