"""Comprobaciones de la evidencia histórica de los finalistas, sin entrenar."""
import csv
from pathlib import Path

import pytest

from ptcg_wp.finalist_evidence import b3_selected_candidate, selected_train_count, verify_full_train

ROOT = Path(__file__).resolve().parents[1] / 'results'


@pytest.mark.parametrize(('scenario', 'expected'), [('A', 33066), ('B', 27643), ('C', 33013)])
def test_original_val_rows_record_all_train_games(scenario, expected):
    assert selected_train_count(ROOT / 'baseline2' / f'b2_val_{scenario}.csv', scenario, 'B2') == expected
    assert selected_train_count(ROOT / 'baseline3' / f'b3_val_{scenario}.csv', scenario, 'B3') == expected


@pytest.mark.parametrize(('scenario', 'candidate_file'), [
    ('B', 'b3_candidatas.csv'), ('C', 'b3_candidatas (1).csv'),
])
def test_regeneration_candidate_contains_original_cv_scores(scenario, candidate_file):
    candidate = b3_selected_candidate(ROOT / 'baseline3' / f'b3_cv_{scenario}.csv', scenario)
    with (ROOT / 'baseline3' / candidate_file).open(newline='', encoding='utf-8') as f:
        original = next(row for row in csv.DictReader(f)
                        if row['modelo'] == 'B3_bosque' and row['seleccionada_por'] == 'log_loss')
    assert candidate['trial'] == 1
    for metric in ('auc', 'log_loss', 'brier'):
        assert candidate[metric] == pytest.approx(float(original[metric]))


def test_a_candidate_has_all_metrics_required_by_fitting_function():
    candidate = b3_selected_candidate(ROOT / 'baseline3' / 'b3_cv_A.csv', 'A')
    assert set(('auc', 'log_loss', 'brier', 'seleccionada_por', 'trial')) <= candidate.keys()
    assert candidate['criterion'] == 'gini' and candidate['n_estimators'] == 25


def test_incomplete_training_is_not_accepted_as_full_train():
    metadata = {'escenario': 'A', 'modelo': 'B3_bosque', 'partidas_train_disponibles': 33066,
                'partidas_train_muestra': 33066, 'partidas_fit': 1000, 'fraccion_train': 1.0}
    with pytest.raises(ValueError, match='train completo'):
        verify_full_train(metadata, 'A', 'B3', 33066)
