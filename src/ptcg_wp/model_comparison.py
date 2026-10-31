"""Comparación de AUC con remuestreo emparejado por partida."""
import numpy as np


def _auc_sort_plan(y, probability, codes):
    """Ordena una sola vez para reutilizar el orden en los remuestreos por partida."""
    order = np.argsort(probability, kind='mergesort')
    scores = np.asarray(probability)[order]
    groups = np.asarray(codes)[order]
    weights = 1.0 / np.bincount(codes)[groups]
    starts = np.flatnonzero(np.r_[True, scores[1:] != scores[:-1]])
    return np.asarray(y)[order], groups, weights, starts


def _auc_from_plan(plan, multiplicity):
    y, groups, base_weights, starts = plan
    w = base_weights * multiplicity[groups]
    positive = np.add.reduceat(w * y, starts)
    negative = np.add.reduceat(w * (1-y), starts)
    denominator = positive.sum() * negative.sum()
    if denominator == 0:
        return np.nan
    return float(np.sum(positive * (np.cumsum(negative) - .5 * negative)) / denominator)


def paired_game_auc_bootstrap(y, reference, candidate, codes, n_boot=1000, seed=2026):
    """Diferencia candidata-referencia: mismas partidas sorteadas en ambos modelos.

    Cada partida sorteada suma su multiplicidad; sus filas conservan peso 1/n.
    Los intervalos percentiles del 95 % son por escenario, no simultáneos.
    """
    y, codes = np.asarray(y), np.asarray(codes)
    if len(y) == 0 or len(y) != len(reference) or len(y) != len(candidate) or len(y) != len(codes):
        raise ValueError('Las predicciones emparejadas deben corresponder a las mismas filas.')
    if (not np.isin(y, [0, 1]).all() or len(np.unique(y)) != 2
            or not np.isfinite(reference).all() or not np.isfinite(candidate).all()):
        raise ValueError('Se requieren etiquetas binarias y probabilidades finitas.')
    if (not np.issubdtype(codes.dtype, np.integer)):
        raise ValueError('Los códigos de partida deben ser enteros.')
    if n_boot < 100 or codes.min() < 0 or set(np.unique(codes)) != set(range(int(codes.max())+1)):
        raise ValueError('Se necesitan al menos 100 réplicas y códigos de partida contiguos desde 0.')
    n_games = int(codes.max())+1
    if n_games < 2: raise ValueError('Se necesitan al menos dos partidas.')
    ref_plan = _auc_sort_plan(y, reference, codes)
    cand_plan = _auc_sort_plan(y, candidate, codes)
    rng = np.random.default_rng(seed)
    differences = np.empty(n_boot)
    for i in range(n_boot):
        counts = rng.multinomial(n_games, np.full(n_games, 1/n_games))
        differences[i] = _auc_from_plan(cand_plan, counts) - _auc_from_plan(ref_plan, counts)
    valid = differences[np.isfinite(differences)]
    if len(valid) < .95*n_boot:
        raise ValueError('Demasiadas réplicas sin ambas clases; revisar las partidas de validación.')
    lower, upper = np.quantile(valid, [.025, .975])
    return {'delta_auc_ci_lower': float(lower), 'delta_auc_ci_upper': float(upper),
            'bootstrap_replicates': n_boot, 'bootstrap_valid': len(valid),
            'confidence': .95, 'interval': 'percentile', 'seed': seed}, differences
