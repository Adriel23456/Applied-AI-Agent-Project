"""B0 y B1: las dos lineas base mas simples, ajustadas por lotes con ScenarioStream.

- B0: probabilidad a priori (fraccion de partidas ganadas por quien actua en train).
- B1: puntuacion fija de recursos convertida en probabilidad con una logistica de una
  variable ajustada en train.
"""

import numpy as np
from scipy.special import expit, logit

from ptcg_wp.data import weights_by_game


def b1_score(frame, hp_unit):
    """Puntuación fija de recursos adoptada para B1."""
    prize_advantage = frame["opp_prizes"] - frame["own_prizes"]
    return (prize_advantage + frame["diff_total_hp"] / hp_unit + frame["diff_bench_n"]).to_numpy(float)


def b0_and_hp_unit(stream):
    """Calcula B0 y la unidad de PV de B1 usando solo los días de train."""
    game_win_share = []
    hp_sum = 0.0
    hp_weight = 0.0
    for day in stream:
        train = day.loc[day["split"] == "train"]
        by_game = train.groupby("game_id", sort=False)["y"].agg(["sum", "count"])
        game_win_share.append((by_game["sum"] / by_game["count"]).to_numpy())

        w = weights_by_game(train["game_id"])
        hp = np.concatenate((train["own_active_max_hp"].to_numpy(),
                             train["opp_active_max_hp"].to_numpy()))
        hp_w = np.concatenate((w, w))
        valid = hp > 0
        hp_sum += np.dot(hp[valid], hp_w[valid])
        hp_weight += hp_w[valid].sum()
    return float(np.concatenate(game_win_share).mean()), float(hp_sum / hp_weight)


def fit_b1_mapping(stream, hp_unit, base_probability, max_iter=6, tolerance=1e-8):
    """Ajusta la sigmoide de B1 por Newton-Raphson, sin guardar train completo.

    Es la misma regresión logística de una variable que se usaba en el cuaderno,
    calculada por días para no agotar la RAM.
    """
    beta = np.array([logit(np.clip(base_probability, 1e-8, 1 - 1e-8)), 0.0])
    for _ in range(max_iter):
        gradient = np.zeros(2)
        hessian = np.zeros((2, 2))
        for day in stream:
            train = day.loc[day["split"] == "train"]
            score = b1_score(train, hp_unit)
            y = train["y"].to_numpy(float)
            w = weights_by_game(train["game_id"])
            probability = expit(beta[0] + beta[1] * score)
            residual = w * (y - probability)
            gradient += (residual.sum(), np.dot(residual, score))
            curvature = w * probability * (1 - probability)
            hessian += ((curvature.sum(), np.dot(curvature, score)),
                        (np.dot(curvature, score), np.dot(curvature, score * score)))
        step = np.linalg.solve(hessian + 1e-10 * np.eye(2), gradient)
        beta += step
        if np.max(np.abs(step)) < tolerance:
            break
    return beta


def b1_probability(frame, hp_unit, beta):
    """Convierte el score fijo de B1 a probabilidad con la sigmoide ajustada."""
    score = b1_score(frame, hp_unit)
    return expit(beta[0] + beta[1] * score)
