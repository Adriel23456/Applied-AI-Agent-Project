"""Comprobaciones de la evidencia historica de los finalistas, sin entrenar.

Los resultados ya no viven en el repo: se bajan de Kaggle a /content/resultados (o a la
carpeta de la variable PTCG_RESULTADOS). Si no estan, estas pruebas se omiten.
"""
import csv
import os
from pathlib import Path

import pytest

from ptcg_wp.finalist_evidence import b3_selected_candidate, selected_train_count, verify_full_train

_REPO_RESULTS = Path(__file__).resolve().parents[1] / 'results'
ROOT = Path(os.environ.get('PTCG_RESULTADOS', '/content/resultados'))
if not (ROOT / 'b3' / 'busqueda' / 'b3_cv_A.csv').exists() and (_REPO_RESULTS / 'b3').exists():
    ROOT = _REPO_RESULTS
pytestmark = pytest.mark.skipif(
    not all((ROOT / r).exists() for r in (
        'b2/final/escenario_A/b2_val_A.csv', 'b3/busqueda/b3_cv_A.csv',
        'b3/busqueda/b3_candidatas_C.csv', 'b3/final/escenario_C/b3_val_C.csv')),
    reason='resultados de B2/B3 no disponibles localmente (se bajan de Kaggle)')


@pytest.mark.parametrize(('scenario', 'expected'), [('A', 33066), ('B', 27643), ('C', 33013)])
def test_original_val_rows_record_all_train_games(scenario, expected):
    assert selected_train_count(ROOT / 'b2' / 'final' / f'escenario_{scenario}' / f'b2_val_{scenario}.csv', scenario, 'B2') == expected
    assert selected_train_count(ROOT / 'b3' / 'final' / f'escenario_{scenario}' / f'b3_val_{scenario}.csv', scenario, 'B3') == expected


@pytest.mark.parametrize(('scenario', 'candidate_file'), [
    ('B', 'b3_candidatas_B.csv'), ('C', 'b3_candidatas_C.csv'),
])
def test_regeneration_candidate_contains_original_cv_scores(scenario, candidate_file):
    candidate = b3_selected_candidate(ROOT / 'b3' / 'busqueda' / f'b3_cv_{scenario}.csv', scenario)
    with (ROOT / 'b3' / 'busqueda' / candidate_file).open(newline='', encoding='utf-8') as f:
        original = next(row for row in csv.DictReader(f)
                        if row['modelo'] == 'B3_bosque' and row['seleccionada_por'] == 'log_loss')
    assert candidate['trial'] == 1
    for metric in ('auc', 'log_loss', 'brier'):
        assert candidate[metric] == pytest.approx(float(original[metric]))


def test_a_candidate_has_all_metrics_required_by_fitting_function():
    candidate = b3_selected_candidate(ROOT / 'b3' / 'busqueda' / 'b3_cv_A.csv', 'A')
    assert set(('auc', 'log_loss', 'brier', 'seleccionada_por', 'trial')) <= candidate.keys()
    assert candidate['criterion'] == 'gini' and candidate['n_estimators'] == 25


def test_incomplete_training_is_not_accepted_as_full_train():
    metadata = {'escenario': 'A', 'modelo': 'B3_bosque', 'partidas_train_disponibles': 33066,
                'partidas_train_muestra': 33066, 'partidas_fit': 1000, 'fraccion_train': 1.0}
    with pytest.raises(ValueError, match='train completo'):
        verify_full_train(metadata, 'A', 'B3', 33066)
