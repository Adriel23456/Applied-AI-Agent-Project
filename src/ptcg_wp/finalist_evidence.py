"""Evidencia de los ajustes seleccionados de B2/B3, sin entrenar modelos."""
import csv
import math
from pathlib import Path
from statistics import fmean

B3_PARAMS = {'criterion': 'gini', 'max_depth': 12, 'min_samples_leaf': 20,
             'n_estimators': 25, 'max_features': 0.5}
METRICS = ('auc', 'log_loss', 'brier')


def _rows(path):
    with Path(path).open(encoding='utf-8', newline='') as source:
        return list(csv.DictReader(source))


def b3_selected_candidate(cv_path, scenario):
    """Reconstruye una finalista completa desde sus cinco pliegues de CV registrados."""
    if scenario not in ('A', 'B', 'C'):
        raise ValueError('El escenario debe ser A, B o C')
    rows = [r for r in _rows(cv_path) if r['escenario'] == scenario
            and r['modelo'] == 'B3_bosque' and r['estudio'] == 'log_loss'
            and int(r['trial']) == 1 and r['etapa'] == 'global']
    if len(rows) != 5 or {int(r['fold']) for r in rows} != {1, 2, 3, 4, 5}:
        raise ValueError(f'B3 {scenario}: se requieren exactamente los cinco pliegues CV de la finalista')
    for row in rows:
        if (row['criterion'] != B3_PARAMS['criterion']
                or int(float(row['max_depth'])) != B3_PARAMS['max_depth']
                or int(float(row['min_samples_leaf'])) != B3_PARAMS['min_samples_leaf']
                or int(float(row['n_estimators'])) != B3_PARAMS['n_estimators']
                or float(row['max_features']) != B3_PARAMS['max_features']):
            raise ValueError(f'B3 {scenario}: los hiperparámetros CV no coinciden con la finalista')
    scores = {metric: fmean(float(row[metric]) for row in rows) for metric in METRICS}
    if not all(math.isfinite(value) for value in scores.values()):
        raise ValueError(f'B3 {scenario}: las métricas CV deben ser finitas')
    return {'escenario': scenario, 'modelo': 'B3_bosque', 'seleccionada_por': 'log_loss',
            'trial': 1, **B3_PARAMS, **scores}


def verify_full_train(metadata, scenario, baseline, expected_games):
    """Comprueba el registro del ajuste, no examina ni reevalúa el dataset."""
    if baseline not in ('B2', 'B3') or scenario not in ('A', 'B', 'C'):
        raise ValueError('Baseline o escenario inválido')
    expected_model = 'B2' if baseline == 'B2' else 'B3_bosque'
    fit_field = 'n_partidas_fit' if baseline == 'B2' else 'partidas_fit'
    try:
        valid = (metadata['escenario'] == scenario and metadata['modelo'] == expected_model
                 and int(metadata['partidas_train_disponibles']) == int(expected_games)
                 and int(metadata['partidas_train_muestra']) == int(expected_games)
                 and int(metadata[fit_field]) == int(expected_games)
                 and float(metadata['fraccion_train']) == 1.0)
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f'{baseline} {scenario}: faltan metadatos válidos del ajuste completo') from exc
    if not valid:
        raise ValueError(f'{baseline} {scenario}: el artefacto no acredita el train completo registrado')
    return int(expected_games)


def selected_train_count(val_path, scenario, baseline):
    """Obtiene el tamaño de train de la fila global de val del finalista seleccionado."""
    if baseline not in ('B2', 'B3') or scenario not in ('A', 'B', 'C'):
        raise ValueError('Baseline o escenario inválido')
    rows = [r for r in _rows(val_path) if r['escenario'] == scenario and r['etapa'] == 'global'
            and ((baseline == 'B2' and r['modelo'] == 'B2' and float(r['C']) == 0.1)
                 or (baseline == 'B3' and r['modelo'] == 'B3_bosque'
                     and r['seleccionada_por'] == 'log_loss' and int(r['trial']) == 1))]
    if len(rows) != 1:
        raise ValueError(f'{baseline} {scenario}: se esperaba una fila global del finalista')
    expected = int(rows[0]['partidas_train_disponibles'])
    return verify_full_train(rows[0], scenario, baseline, expected)
