"""Modelo final: de observacion a probabilidad con las MISMAS caracteristicas del entrenamiento."""

from pathlib import Path
import copy
import json
import sys

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn import __version__ as sklearn_version
from sklearn.ensemble import HistGradientBoostingClassifier

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ptcg_wp.features import feature_columns, game_rows  # noqa: E402
from ptcg_wp import predictor as pred  # noqa: E402
from test_fuga import game  # noqa: E402


def _partidas():
    """Partidas sinteticas variadas: premios y PV distintos segun el ganador."""
    rng = np.random.default_rng(1)
    partidas = []
    for k in range(30):
        g = game(rewards=(1, -1) if k % 2 else (-1, 1), turns=(0, 1, 1, 2, 2, 3, 3, 4))
        g["info"]["EpisodeId"] = k
        for paso in g["steps"]:
            for entrada in paso:
                cur = entrada["observation"]["current"]
                if cur:
                    cur["players"][0]["prize"] = [None] * int(rng.integers(1, 7))
                    cur["players"][1]["active"][0]["hp"] = int(rng.integers(10, 100))
        partidas.append(g)
    return partidas


@pytest.fixture
def entorno(tmp_path):
    filas = pd.DataFrame([r for g in _partidas() for r in game_rows(g, "d")])
    features = feature_columns(filas.columns)
    utiles = filas[(filas.setup == 0) & (filas.decided == 0)]
    modelo = HistGradientBoostingClassifier(max_iter=20, min_samples_leaf=5).fit(
        utiles[features].to_numpy(np.float32), utiles.y)
    artefacto = {"model": modelo, "features": features, "n_iter_vigilancia": 20,
                 "candidata": {"trial": 20}, "version_sklearn": sklearn_version}
    raiz = tmp_path / "res"
    (raiz / pred.MODELO_ORIGEN).parent.mkdir(parents=True)
    joblib.dump(artefacto, raiz / pred.MODELO_ORIGEN)
    pd.DataFrame([{"etapa": "global", "auc": 0.8}]).to_csv(raiz / pred.METRICAS_ORIGEN, index=False)
    return raiz, artefacto, filas, utiles, features


def test_observacion_da_las_mismas_caracteristicas_y_probabilidad(entorno):
    raiz, artefacto, filas, utiles, features = entorno
    p = pred.PredictorVictoria(artefacto)
    tabla = p.probabilidades_tabla(utiles)
    i = 0
    for g in _partidas():
        for paso in g["steps"]:
            entrada = next(e for e in paso if e["status"] == "ACTIVE")
            cur = entrada["observation"]["current"]
            if pred.estado_de(cur) != "modelo":
                continue
            fila = utiles.iloc[i]
            assert np.array_equal(p.caracteristicas(cur)[0], fila[features].to_numpy(np.float32))
            # Acepta tambien la observacion completa con la clave "current"
            assert p.probabilidad(entrada["observation"]) == pytest.approx(tabla[i])
            i += 1
    assert i == len(utiles)


def test_estados_sin_prediccion(entorno):
    _, artefacto, *_ = entorno
    p = pred.PredictorVictoria(artefacto)
    g = game()
    preparacion = g["steps"][0][0]["observation"]["current"]
    assert p.evaluar(preparacion) == {"probabilidad": None, "estado": "preparacion", "turno": 0, "jugador": 0}
    decidido = copy.deepcopy(g["steps"][2][0]["observation"]["current"])
    decidido["players"][1]["prize"] = []
    assert p.probabilidad(decidido) is None and pred.estado_de(decidido) == "decidido"
    with pytest.raises(ValueError):
        p.probabilidad({"sin": "current"})


def test_exportar_y_cargar(entorno):
    raiz, artefacto, _, utiles, _ = entorno
    rutas = pred.exportar_modelo_final(raiz, commit="abc1234")
    assert rutas == [pred.MODELO_EXPORTADO, pred.FICHA_EXPORTADA]
    ficha = json.loads((raiz / pred.FICHA_EXPORTADA).read_text())
    assert ficha["escenario_de_entrenamiento"] == "A" and ficha["commit"] == "abc1234"
    assert ficha["n_caracteristicas"] == len(artefacto["features"])
    cargado = pred.PredictorVictoria.cargar(raiz / pred.MODELO_EXPORTADO)
    assert np.allclose(cargado.probabilidades_tabla(utiles), pred.PredictorVictoria(artefacto).probabilidades_tabla(utiles))


def test_version_distinta_de_sklearn_se_rechaza(entorno):
    _, artefacto, *_ = entorno
    with pytest.raises(RuntimeError, match="scikit-learn"):
        pred.PredictorVictoria({**artefacto, "version_sklearn": "0.0.1"})
