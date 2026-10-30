"""Demostracion de fuga en B2: division por fila contra division por partida.

Misma muestra de partidas de train, mismo ajuste (LBFGS, C fijo) y dos reglas de division.
La division por fila deja partidas en ambos lados; la division por partida no.
"""
from pathlib import Path
import json
import time

import numpy as np
import pandas as pd
from sklearn import __version__ as sklearn_version
from sklearn.model_selection import GroupShuffleSplit, train_test_split

from ptcg_wp.b2 import _collect_rows, _metric_rows, _pipeline, sample_train_games
from ptcg_wp.data import weights_by_game


def leakage_comparison(stream, features, output_dir, seed=2026, max_games=200, c_value=0.1):
    """Misma muestra de train y mismo ajuste LBFGS, con dos reglas de división."""
    start = time.perf_counter()
    games = sample_train_games(stream, max_games, seed)
    x, y, groups, stages = _collect_rows(stream, features, 'train', games)
    indices = np.arange(len(y))
    row_fit, row_eval = train_test_split(indices, test_size=0.2, random_state=seed, stratify=y)
    group_fit, group_eval = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
                                 .split(x, y, groups))
    rows, overlaps = [], []
    for name, fit, held in [('fila', row_fit, row_eval), ('partida', group_fit, group_eval)]:
        model = _pipeline(c_value, 300)
        w = weights_by_game(groups[fit])
        model.fit(x[fit], y[fit], scale__sample_weight=w, logit__sample_weight=w)
        common = {'escenario': stream.scenario, 'division': name, 'C': c_value, 'semilla': seed}
        rows.extend(_metric_rows(y[held], model.predict_proba(x[held])[:, 1],
                                 groups[held], stages[held], common))
        fit_games, held_games = np.unique(groups[fit]), np.unique(groups[held])
        overlap = np.intersect1d(fit_games, held_games)
        overlaps.append({**common, 'partidas_ajuste': len(fit_games), 'partidas_evaluacion': len(held_games),
                         'partidas_en_ambos_lados': len(overlap),
                         'fraccion_evaluacion_con_partida_vista': len(overlap) / len(held_games),
                         'n_iter': int(model.named_steps['logit'].n_iter_[0])})
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / 'metricas.csv', index=False)
    pd.DataFrame(overlaps).to_csv(out / 'solapamiento.csv', index=False)
    (out / 'config.json').write_text(json.dumps({'scenario': stream.scenario, 'seed': seed,
        'max_games': max_games, 'sample_games': len(np.unique(groups)), 'C': c_value,
        'max_iter': 300, 'held_fraction': 0.2, 'features': list(features),
        'sklearn_version': sklearn_version, 'seconds': time.perf_counter()-start}, indent=2))
    return pd.DataFrame(rows), pd.DataFrame(overlaps)
