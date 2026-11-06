"""Evaluacion comun: una sola implementacion para todos los modelos, igual a scikit-learn."""

from pathlib import Path
import sys

import numpy as np
import pytest
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ptcg_wp import b3, b4  # noqa: E402
from ptcg_wp.evaluation import STAGES, metric_rows, metric_rows_codes  # noqa: E402


@pytest.fixture
def datos():
    rng = np.random.default_rng(4)
    n = 3000
    grupos = rng.integers(0, 120, size=n)
    etapas = rng.integers(0, 3, size=n)
    y = (rng.random(n) < 0.5).astype(int)
    # Probabilidades redondeadas: fuerza empates, el caso delicado del AUC
    p = np.round(np.clip(0.5 + 0.3 * (y - 0.5) + rng.normal(0, 0.25, n), 0.01, 0.99), 2)
    return y, p, grupos, etapas


def _referencia(y, p, grupos):
    _, inverse, counts = np.unique(grupos, return_inverse=True, return_counts=True)
    w = 1.0 / counts[inverse]
    return (roc_auc_score(y, p, sample_weight=w), log_loss(y, p, sample_weight=w, labels=[0, 1]),
            brier_score_loss(y, p, sample_weight=w))


def test_igual_a_sklearn_global_y_por_etapa(datos):
    y, p, grupos, etapas = datos
    filas = metric_rows_codes(y, p, grupos, etapas, {"modelo": "x"})
    assert [f["etapa"] for f in filas] == ["global", *STAGES]
    for fila in filas:
        mascara = np.ones(len(y), bool) if fila["etapa"] == "global" else etapas == STAGES.index(fila["etapa"])
        auc, ll, brier = _referencia(y[mascara], p[mascara], grupos[mascara])
        assert fila["auc"] == pytest.approx(auc, abs=1e-12)
        assert fila["log_loss"] == pytest.approx(ll, abs=1e-12)
        assert fila["brier"] == pytest.approx(brier, abs=1e-12)
        assert fila["n_estados"] == mascara.sum()
        assert fila["n_partidas"] == len(np.unique(grupos[mascara]))
        assert fila["modelo"] == "x"


def test_ids_y_etapas_en_texto_dan_lo_mismo(datos):
    y, p, grupos, etapas = datos
    ids = np.array([f"partida_{g}" for g in grupos], dtype=object)
    texto = np.array([STAGES[e] for e in etapas], dtype=object)
    assert metric_rows(y, p, ids, texto, {}) == metric_rows_codes(y, p, grupos, etapas, {})


def test_solo_global_y_validaciones(datos):
    y, p, grupos, _ = datos
    filas = metric_rows_codes(y, p, grupos, None, {}, include_stages=False)
    assert [f["etapa"] for f in filas] == ["global"]
    with pytest.raises(ValueError):
        metric_rows_codes(y, p[:-1], grupos, None, {}, include_stages=False)


def test_b3_y_b4_usan_la_funcion_comun(datos):
    y, p, grupos, _ = datos
    assert b4.metric_rows_codes is metric_rows_codes
    assert b3._global_metrics(y, p, grupos, {}) == metric_rows_codes(y, p, grupos, None, {}, include_stages=False)[0]
