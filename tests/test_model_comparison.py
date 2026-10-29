"""Contrasta el AUC eficiente con una definición independiente por pares."""
import numpy as np
import pytest

from ptcg_wp.model_comparison import (_auc_sort_plan, _auc_from_plan,
                                      paired_game_auc_bootstrap)


def pairwise_auc(y, p, codes, multiplicity):
    w = multiplicity[codes] / np.bincount(codes)[codes]
    pos, neg = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
    numerator = sum(w[i]*w[j]*(float(p[i] > p[j]) + .5*float(p[i] == p[j]))
                    for i in pos for j in neg)
    return numerator / (w[pos].sum()*w[neg].sum())


def test_auc_matches_pairwise_definition_with_ties_and_unequal_game_lengths():
    y = np.array([0, 1, 1, 0, 1, 0, 1])
    p = np.array([.2, .5, .5, .5, .8, .4, .7])
    codes = np.array([0, 0, 1, 1, 1, 2, 2])
    multiplicity = np.array([2, 0, 1])
    plan = _auc_sort_plan(y, p, codes)
    assert _auc_from_plan(plan, multiplicity) == pytest.approx(pairwise_auc(y, p, codes, multiplicity))


def test_identical_models_have_zero_paired_interval():
    y = np.tile([0, 1], 6)
    codes = np.repeat(np.arange(6), 2)
    p = np.tile([.3, .8], 6)
    info, draws = paired_game_auc_bootstrap(y, p, p, codes, n_boot=100)
    assert np.all(draws == 0)
    assert info['delta_auc_ci_lower'] == 0 == info['delta_auc_ci_upper']


def test_perfect_model_against_reversed_scores_improves_auc_by_one():
    y = np.tile([0, 1], 6)
    codes = np.repeat(np.arange(6), 2)
    info, draws = paired_game_auc_bootstrap(y, 1-y, y, codes, n_boot=100)
    assert np.allclose(draws, 1)
    assert info['delta_auc_ci_lower'] == pytest.approx(1)
    assert info['delta_auc_ci_upper'] == pytest.approx(1)


def test_bootstrap_rejects_unpaired_rows():
    with pytest.raises(ValueError, match='mismas filas'):
        paired_game_auc_bootstrap(np.array([0, 1]), [0], [0, 1], np.array([0, 1]), n_boot=100)
