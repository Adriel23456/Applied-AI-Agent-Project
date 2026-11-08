"""Validacion del agente (rama 08): seleccion de casos, extraccion y bateria N1.

Usa el modelo sintetico de test_agente.py y repeticiones sinteticas, sin Kaggle ni red.
"""

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ptcg_agente.validacion import bateria, casos, resumen  # noqa: E402
from ptcg_wp.features import game_rows  # noqa: E402
from test_agente import _partidas, modelo, raiz  # noqa: E402,F401

N = 4


@pytest.fixture(scope="module")
def partidas():
    return {g["info"]["EpisodeId"]: g for g in _partidas(24)}


@pytest.fixture(scope="module")
def tabla(modelo, partidas):  # noqa: F811
    filas = pd.DataFrame([r for g in partidas.values() for r in game_rows(g, "d")])
    filas = filas[(filas.setup == 0) & (filas.decided == 0)].reset_index(drop=True)
    filas["stage"] = [modelo.etapa(t) for t in filas["turn"]]
    filas["p"] = modelo.predictor.probabilidades_tabla(filas)
    filas["en_B"] = filas["game_id"] % 3 == 1
    filas["en_C"] = filas["game_id"] % 3 == 2
    return filas[["game_id", "day", "step", "turn", "stage", "y", "p", "en_B", "en_C"]]


@pytest.fixture(scope="module")
def datos(tabla, partidas, tmp_path_factory):
    elegidos = casos.elegir(tabla, n=N, n_errores=2)
    raiz_v = tmp_path_factory.mktemp("validacion")
    original = casos.bajar_partida

    def falsa(dia, game_id, carpeta):
        ruta = Path(carpeta) / f"{int(game_id)}.json"
        ruta.write_text(json.dumps(partidas[int(game_id)]), encoding="utf-8")
        return ruta

    casos.bajar_partida = falsa
    try:
        casos.extraer(elegidos, ("d", int(elegidos["game_id"].iloc[0])), raiz_v)
    finally:
        casos.bajar_partida = original
    return casos.Datos(raiz_v)


def test_eleccion_respeta_las_reglas_del_protocolo(tabla):
    a = casos.elegir(tabla, n=N, n_errores=2)
    b = casos.elegir(tabla, n=N, n_errores=2)
    pd.testing.assert_frame_equal(a, b)  # misma semilla, mismos casos
    for grupo in ("normal_A", "poblacion_B", "poblacion_C"):
        sub = a[a["grupo"] == grupo]
        assert len(sub) == 3 * N and sub.groupby("stage")["game_id"].nunique().eq(N).all()
    assert a.loc[a["grupo"] == "poblacion_B", "en_B"].all() and a.loc[a["grupo"] == "poblacion_C", "en_C"].all()
    normales = set(a.loc[a["grupo"] == "normal_A", "game_id"])
    assert normales.isdisjoint(a.loc[a["grupo"].str.startswith("poblacion"), "game_id"])
    errores = a[a["grupo"].str.startswith("error_")]
    assert (((errores["p"] >= 0.9) & (errores["y"] == 0)) | ((errores["p"] <= 0.1) & (errores["y"] == 1))).all()


def test_extraccion_guarda_la_observacion_de_cada_caso(datos, tabla, modelo):  # noqa: F811
    for _, f in datos.casos.iterrows():
        assert modelo.predictor.probabilidad(datos.obs(f["caso"])) == pytest.approx(f["p"], abs=1e-6)
    assert datos.obs("preparacion")["turn"] == 0
    assert datos.larga in datos.repeticiones


def test_bateria_n1_completa_sin_excepciones(datos, modelo):  # noqa: F811
    resultados, detalle, latencias = bateria.correr_n1(modelo, datos)
    por_caso = resultados.set_index("caso")
    assert not resultados["excepcion"].any(), resultados[resultados["excepcion"]]["obtenido"].tolist()
    deben_aprobar = ["N-01", "N-02", "N-03", "N-04", "N-06", "L-01", "L-02", "L-03", "L-04", "L-05",
                     "L-06", "L-07", "L-08", "L-09", "E-01", "E-02", "E-03", "E-04", "E-05", "E-06",
                     "E-07", "E-08", "E-09", "S-02", "S-03", "S-04", "S-05", "D-01", "D-02", "R-01"]
    fallidos = {c: por_caso.loc[c, "obtenido"] for c in deben_aprobar if por_caso.loc[c, "aprobado"] is not True}
    assert not fallidos, fallidos
    assert por_caso.loc["M-01", "aprobado"] is not False and pd.isna(por_caso.loc["M-02", "aprobado"])
    assert len(detalle) >= 3 * 3 * N and set(latencias["herramienta"]) >= {"estimar_probabilidad", "evaluar_partida"}
    m = resumen.metricas(resultados, latencias)
    assert {"Advertencias cuando corresponden", "Rechazos correctos", "Robustez"} <= set(m["metrica"])
    assert set(resumen.por_grupo(resultados).index) >= {"normales", "limite", "entradas", "errores"}