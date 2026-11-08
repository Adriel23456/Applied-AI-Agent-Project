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
        casos.extraer(elegidos, ("d", int(elegidos["game_id"].iloc[0])), raiz_v, pausa_s=0)
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
                     "L-06", "L-07", "L-08", "L-09", "L-10", "E-01", "E-02", "E-03", "E-04", "E-05", "E-06",
                     "E-07", "E-08", "E-09", "S-02", "S-03", "S-04", "S-05", "D-01", "D-02", "R-01"]
    fallidos = {c: por_caso.loc[c, "obtenido"] for c in deben_aprobar if por_caso.loc[c, "aprobado"] is not True}
    assert not fallidos, fallidos
    assert por_caso.loc["M-01", "aprobado"] is not False and pd.isna(por_caso.loc["M-02", "aprobado"])
    assert len(detalle) >= 3 * 3 * N and set(latencias["herramienta"]) >= {"estimar_probabilidad", "evaluar_partida"}
    m = resumen.metricas(resultados, latencias)
    assert {"Advertencias cuando corresponden", "Rechazos correctos", "Robustez"} <= set(m["metrica"])
    assert set(resumen.por_grupo(resultados).index) >= {"normales", "limite", "entradas", "errores"}

def test_bajar_partida_reintenta_si_kaggle_pide_esperar(tmp_path, monkeypatch):
    respuestas = iter([(False, "429 Client Error: Too Many Requests"), (False, "404"), (True, "")])

    def falsa(dataset, nombre, destino):
        ok, texto = next(respuestas)
        if ok:
            Path(destino).write_text("{}", encoding="utf-8")
        return ok, texto

    monkeypatch.setattr(casos.store, "_bajar_archivo", falsa)
    monkeypatch.setattr(casos.time, "sleep", lambda s: None)
    assert casos.bajar_partida("d", 7, tmp_path).exists()

def test_n2_corre_todas_las_consultas_con_un_llm_de_prueba(datos, modelo, partidas, tmp_path):  # noqa: F811
    from ptcg_agente.registro import Registro
    from ptcg_agente.validacion import consultas
    from test_agente import LLMFalso

    ejemplos = []
    for g in list(partidas)[:3]:
        ruta = tmp_path / f"partida_{g}.json"
        ruta.write_text(json.dumps(partidas[g]), encoding="utf-8")
        ejemplos.append(ruta)
    lista = consultas.armar(modelo, datos, ejemplos, tmp_path)
    ids = [c.id for c in lista]
    assert sum(i.startswith("A-") for i in ids) == 18 and {"Q-01", "Q-05", "Q-07"} <= set(ids)
    sin_plan = {"objetivo": "", "pasos": []}  # plan invalido: el orquestador usa el plan por defecto
    llm = LLMFalso([sin_plan] * 200, ["Es una estimacion. No tengo acceso a la mano del rival."] * 200)
    tabla = consultas.correr_n2(modelo, datos, ejemplos, Registro("n2", carpeta=tmp_path / "reg"),
                                llm=llm, consultas=lista, avance=None)
    assert len(tabla) == len(lista) and not tabla["excepcion"].any(), tabla[tabla["excepcion"]]["obtenido"].tolist()
    assert tabla["verificada"].all()
    q05 = tabla.set_index("id").loc["Q-05"]
    assert "texto inyectado en salidas de herramientas: False" in q05["obtenido"]
    assert set(consultas.metricas_n2(tabla)["metrica"]) >= {"Herramienta correcta (A-01 a A-06)"}

def test_reconstruir_exige_la_misma_eleccion(tabla):
    a = casos.elegir(tabla, n=N, n_errores=2)
    casos.comprobar_misma_eleccion(None, a)
    casos.comprobar_misma_eleccion(a.assign(larga=False), a)
    otra = a.copy()
    otra.loc[0, "step"] += 1
    with pytest.raises(RuntimeError):
        casos.comprobar_misma_eleccion(otra, a)

def test_n2_salta_repeticiones_que_no_llegan_a_la_etapa_final(modelo, partidas, tmp_path):  # noqa: F811
    from ptcg_agente.validacion import consultas
    from test_fuga import game
    corta = game(rewards=(1, -1), turns=(0, 1, 1, 2, 2, 3, 6, 6))  # termina antes de la etapa final
    ruta_corta = tmp_path / "corta.json"
    ruta_corta.write_text(json.dumps(corta), encoding="utf-8")
    assert consultas.pasos_clave(modelo, str(ruta_corta)) is None
    largas = []
    for g in list(partidas)[:3]:
        ruta = tmp_path / f"partida_{g}.json"
        ruta.write_text(json.dumps(partidas[g]), encoding="utf-8")
        largas.append(ruta)
    elegidas = consultas.repeticiones_utiles(modelo, [ruta_corta, *largas])
    assert [a for a, _ in elegidas] == [str(r) for r in largas]
    with pytest.raises(RuntimeError):
        consultas.repeticiones_utiles(modelo, [ruta_corta, *largas[:1]])