"""Agente (Etapa 3): herramientas, verificador, artefactos, registro y servidor MCP.

Se arma un modelo sintetico con la misma forma que el modelo final (mismas 62 caracteristicas,
mismo formato de archivos) para que las pruebas corran sin Kaggle ni red.
"""

import asyncio
import copy
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn import __version__ as sklearn_version
from sklearn.ensemble import HistGradientBoostingClassifier

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ptcg_agente import artefactos, dominio  # noqa: E402
from ptcg_agente import herramientas as hz  # noqa: E402
from ptcg_agente.agentes.verificador import verificar_salida, verificar_texto  # noqa: E402
from ptcg_agente.modelo import ModeloAgente  # noqa: E402
from ptcg_agente.registro import Registro  # noqa: E402
from ptcg_wp.features import feature_columns, game_rows  # noqa: E402
from ptcg_wp.predictor import FICHA_EXPORTADA, MODELO_EXPORTADO, PredictorVictoria  # noqa: E402
from ptcg_wp.store import sha256  # noqa: E402
from test_fuga import game  # noqa: E402

TURNOS = (0, 1, 1, 2, 2, 3, 3, 4, 4, 6, 6, 8, 8, 11, 11)


def _partidas(n=40):
    rng = np.random.default_rng(7)
    partidas = []
    for k in range(n):
        g = game(rewards=(1, -1) if k % 2 else (-1, 1), turns=TURNOS)
        g["info"]["EpisodeId"] = k
        for paso in g["steps"]:
            for entrada in paso:
                cur = entrada["observation"]["current"]
                if cur:
                    cur["players"][0]["prize"] = [None] * int(rng.integers(1, 7))
                    cur["players"][1]["prize"] = [None] * int(rng.integers(1, 7))
                    cur["players"][1]["active"][0]["hp"] = int(rng.integers(10, 100))
                    cur["players"][0]["deckCount"] = int(rng.integers(5, 45))
        partidas.append(g)
    return partidas


@pytest.fixture(scope="module")
def raiz(tmp_path_factory):
    raiz = tmp_path_factory.mktemp("artefactos")
    filas = pd.DataFrame([r for g in _partidas() for r in game_rows(g, "d")])
    utiles = filas[(filas.setup == 0) & (filas.decided == 0)].reset_index(drop=True)
    features = feature_columns(filas.columns)
    modelo = HistGradientBoostingClassifier(max_iter=30, min_samples_leaf=5, random_state=0).fit(
        utiles[features].to_numpy(np.float32), utiles.y)
    ficha = {"modelo": "B4 sintetico", "escenario_de_entrenamiento": "A", "version_sklearn": sklearn_version,
             "perspectiva": "jugador que actua", "n_caracteristicas": len(features)}
    (raiz / MODELO_EXPORTADO).parent.mkdir(parents=True)
    joblib.dump({"model": modelo, "features": features, **ficha}, raiz / MODELO_EXPORTADO)
    (raiz / FICHA_EXPORTADA).write_text(json.dumps(ficha), encoding="utf-8")
    perfil = dominio.construir_perfil(utiles, features, (5, 9))
    (raiz / artefactos.DOMINIO).parent.mkdir(parents=True)
    (raiz / artefactos.DOMINIO).write_text(json.dumps(perfil), encoding="utf-8")
    (raiz / artefactos.METRICAS_TEST[0]).parent.mkdir(parents=True)
    for ruta, auc in zip(artefactos.METRICAS_TEST, (0.833, 0.789, 0.787)):
        pd.DataFrame([{"modelo": "B4", "etapa": e, "auc": a, "log_loss": 0.5, "brier": 0.17}
                      for e, a in (("global", auc), ("inicio", 0.684), ("medio", 0.828), ("final", 0.937))]
                     ).to_csv(raiz / ruta, index=False)
    (raiz / artefactos.VEREDICTO).write_text(json.dumps({"H1": "sostenida"}), encoding="utf-8")
    manifiesto = {"archivos": {r: {"sha256": sha256(raiz / r)} for r in artefactos.REQUERIDOS}}
    (raiz / artefactos.MANIFIESTO).write_text(json.dumps(manifiesto), encoding="utf-8")
    return raiz


@pytest.fixture(scope="module")
def modelo(raiz):
    return ModeloAgente.cargar(raiz)


def _estados(etapa=None, modelo=None):
    """Observaciones del jugador que actua con prediccion (opcionalmente de una etapa)."""
    salida = []
    for g in _partidas(6):
        for paso in g["steps"]:
            cur = next(e for e in paso if e["status"] == "ACTIVE")["observation"]["current"]
            if cur["turn"] == 0:
                continue
            if etapa is None or modelo.etapa(cur["turn"]) == etapa:
                salida.append(cur)
    return salida


# ---------- Herramientas ----------

def test_estimar_da_la_misma_probabilidad_que_el_predictor(raiz, modelo):
    predictor = PredictorVictoria.cargar(raiz / MODELO_EXPORTADO)
    for cur in _estados():
        s = hz.llamar(modelo, "estimar_probabilidad", {"observacion": cur})
        assert s["ok"] and s["verificacion"]["aprobado"], s
        assert s["probabilidad"] == pytest.approx(predictor.probabilidad(cur))


def test_advertencia_obligatoria_en_inicio(modelo):
    cur = _estados("inicio", modelo)[0]
    s = hz.llamar(modelo, "estimar_probabilidad", {"observacion": cur})
    assert "etapa_inicio" in {a["codigo"] for a in s["advertencias"]}
    assert s["auc_test_etapa"] == pytest.approx(0.684)


def test_explicacion_suma_el_logit(modelo):
    for cur in _estados()[:10]:
        s = hz.llamar(modelo, "explicar_prediccion", {"observacion": cur, "top": 3})
        assert s["verificacion"]["aprobado"], s["verificacion"]
        assert s["valor_base_logit"] + s["suma_shap"] == pytest.approx(s["logit"], abs=1e-3)
        assert len(s["a_favor"]) <= 3 and len(s["en_contra"]) <= 3
        assert s["texto"].startswith("Probabilidad de victoria:")


def test_preparacion_y_estado_resuelto_no_tienen_probabilidad(modelo):
    g = game()
    prep = g["steps"][0][0]["observation"]["current"]
    s = hz.llamar(modelo, "estimar_probabilidad", {"observacion": prep})
    assert s["probabilidad"] is None and s["estado"] == "preparacion"
    assert [a["codigo"] for a in s["advertencias"]] == ["sin_prediccion"]
    resuelto = copy.deepcopy(g["steps"][2][0]["observation"]["current"])
    resuelto["players"][1]["prize"] = []
    s = hz.llamar(modelo, "explicar_prediccion", {"observacion": resuelto})
    assert s["estado"] == "decidido" and s["probabilidad"] is None and s["verificacion"]["aprobado"]


def test_fuera_de_dominio_por_carta_y_por_valor(modelo):
    cur = copy.deepcopy(_estados("medio", modelo)[0])
    cur["players"][cur["yourIndex"]]["active"][0]["id"] = 99999
    cur["players"][1 - cur["yourIndex"]]["deckCount"] = 500
    r = hz.llamar(modelo, "revisar_dominio", {"observacion": cur})
    tipos = {h["tipo"] for h in r["hallazgos"]}
    assert not r["dentro_del_dominio"] and {"carta_no_vista", "valor_no_visto"} <= tipos
    s = hz.llamar(modelo, "estimar_probabilidad", {"observacion": cur})
    assert "fuera_de_dominio" in {a["codigo"] for a in s["advertencias"]}
    assert s["verificacion"]["aprobado"]


@pytest.mark.parametrize("argumentos, mensaje", [
    ({"observacion": {"turn": 3}}, "le faltan campos"),
    ({"observacion": {"current": None}}, "jugador que espera"),
    ({"archivo": "no_existe.json"}, "no existe"),
    ({}, "indica 'observacion' o 'archivo'"),
])
def test_entradas_invalidas_no_rompen_el_agente(modelo, argumentos, mensaje):
    s = hz.llamar(modelo, "estimar_probabilidad", argumentos)
    assert s["ok"] is False and mensaje in s["error"]


def test_archivo_json_mal_formado_y_repeticion_sin_paso(modelo, tmp_path):
    malo = tmp_path / "malo.json"
    malo.write_text("{no es json", encoding="utf-8")
    assert "no es un JSON valido" in hz.llamar(modelo, "estimar_probabilidad", {"archivo": str(malo)})["error"]
    rep = tmp_path / "partida.json"
    rep.write_text(json.dumps(_partidas(1)[0]), encoding="utf-8")
    assert "indica 'paso'" in hz.llamar(modelo, "estimar_probabilidad", {"archivo": str(rep)})["error"]
    s = hz.llamar(modelo, "estimar_probabilidad", {"archivo": str(rep), "paso": 5})
    assert s["ok"] and s["origen"] == "partida.json#paso5"


def test_evaluar_partida_curva_en_perspectiva_del_jugador_0(raiz, modelo, tmp_path):
    g = _partidas(1)[0]
    rep = tmp_path / "partida.json"
    rep.write_text(json.dumps(g), encoding="utf-8")
    s = hz.llamar(modelo, "evaluar_partida", {"archivo": str(rep)})
    assert s["ok"] and s["verificacion"]["aprobado"]
    predictor = PredictorVictoria.cargar(raiz / MODELO_EXPORTADO)
    for punto in s["curva"]:
        paso = g["steps"][punto["paso"]]
        cur = next(e for e in paso if e["status"] == "ACTIVE")["observation"]["current"]
        p = predictor.probabilidad(cur)
        assert punto["p_jugador0"] == pytest.approx(p if cur["yourIndex"] == 0 else 1 - p, abs=1e-4)
    assert s["ganador_real"] == 1 and s["turnos"][0]["turno"] == 1


def test_comparar_estados(modelo):
    a = _estados("medio", modelo)[0]
    b = copy.deepcopy(a)
    b["players"][1 - a["yourIndex"]]["prize"] = [None]
    s = hz.llamar(modelo, "comparar_estados", {"estados": [
        {"etiqueta": "jugada 1", "observacion": a}, {"etiqueta": "jugada 2", "observacion": b}]})
    assert s["ok"] and s["verificacion"]["aprobado"]
    assert s["estados"][0]["diferencia_vs_primero"] == 0
    assert s["mejor"] in ("jugada 1", "jugada 2")
    otro = next(c for c in _estados() if c["yourIndex"] != a["yourIndex"])
    s = hz.llamar(modelo, "comparar_estados", {"estados": [{"observacion": a}, {"observacion": otro}]})
    assert s["ok"] is False and "jugadores distintos" in s["error"]


def test_describir_modelo(modelo):
    s = hz.llamar(modelo, "describir_modelo")
    assert s["metricas_test_B4"]["A"]["global"]["auc"] == pytest.approx(0.833)
    assert len(s["limites"]) >= 5 and s["verificacion"]["aprobado"]


# ---------- Verificador ----------

def test_verificador_detecta_probabilidad_fuera_de_rango_y_advertencias_faltantes():
    salida = {"ok": True, "estado": "modelo", "probabilidad": 1.3, "etapa": "inicio",
              "dentro_del_dominio": False, "advertencias": []}
    problemas = verificar_salida("estimar_probabilidad", salida)["problemas"]
    assert any("fuera de [0, 1]" in p for p in problemas)
    assert any("etapa_inicio" in p and "fuera_de_dominio" in p for p in problemas)


def test_verificador_detecta_shap_que_no_suma():
    salida = {"ok": True, "estado": "modelo", "probabilidad": 0.6, "etapa": "final", "advertencias": [],
              "valor_base_logit": 0.0, "suma_shap": 1.0, "logit": 0.405465}
    assert any("SHAP no suma" in p for p in verificar_salida("explicar_prediccion", salida)["problemas"])


def test_verificador_de_texto(modelo):
    cur = _estados("inicio", modelo)[0]
    s = hz.llamar(modelo, "estimar_probabilidad", {"observacion": cur})
    p = s["probabilidad_texto"]
    bueno = f"El jugador que actua tiene {p} de ganar, con confianza baja por ser el inicio."
    assert verificar_texto(bueno, [s])["aprobado"]
    assert not verificar_texto(f"Tiene {p} de ganar.", [s])["aprobado"]  # omite la advertencia
    inventado = verificar_texto("Tiene 97.3 % de ganar, con confianza baja.", [s])
    assert any("97.3 %" in x for x in inventado["problemas"])
    promesa = verificar_texto(f"Tiene {p}: garantiza la victoria, con confianza baja.", [s])
    assert any("certeza" in x for x in promesa["problemas"])


def test_verificador_sin_prediccion_no_admite_porcentajes(modelo):
    prep = game()["steps"][0][0]["observation"]["current"]
    s = hz.llamar(modelo, "estimar_probabilidad", {"observacion": prep})
    assert verificar_texto("No hay probabilidad: la partida esta en preparacion.", [s])["aprobado"]
    assert not verificar_texto("Gana con 55 %, aunque el modelo no aplica.", [s])["aprobado"]


# ---------- Artefactos y registro ----------

def test_artefactos_detectan_archivo_alterado(raiz, tmp_path):
    import shutil
    copia = tmp_path / "copia"
    shutil.copytree(raiz, copia)
    (copia / artefactos.VEREDICTO).write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="SHA-256 no coincide"):
        artefactos.verificar(copia)


def test_artefactos_detectan_otra_version_de_sklearn(raiz, tmp_path):
    import shutil
    copia = tmp_path / "copia"
    shutil.copytree(raiz, copia)
    ficha = json.loads((copia / FICHA_EXPORTADA).read_text())
    ficha["version_sklearn"] = "0.0.1"
    (copia / FICHA_EXPORTADA).write_text(json.dumps(ficha))
    manifiesto = json.loads((copia / artefactos.MANIFIESTO).read_text())
    manifiesto["archivos"][FICHA_EXPORTADA]["sha256"] = sha256(copia / FICHA_EXPORTADA)
    (copia / artefactos.MANIFIESTO).write_text(json.dumps(manifiesto))
    with pytest.raises(RuntimeError, match="scikit-learn"):
        artefactos.verificar(copia)


def test_registro_jsonl(modelo, tmp_path):
    registro = Registro("prueba", "abc123", "deadbee", carpeta=tmp_path)
    hz.llamar(modelo, "estimar_probabilidad", {"observacion": _estados()[0]}, registro, agente="ejecutor")
    linea = json.loads(registro.archivo.read_text(encoding="utf-8").splitlines()[-1])
    assert linea["herramienta"] == "estimar_probabilidad" and linea["agente"] == "ejecutor"
    assert linea["modelo_sha256"] == "abc123" and linea["commit"] == "deadbee"
    assert "sha256" in linea["entrada"]["observacion"]  # la observacion se resume, no se copia
    assert linea["salida"]["verificacion"]["aprobado"] and linea["duracion_ms"] >= 0


# ---------- Servidor MCP ----------

def test_servidor_mcp_expone_y_ejecuta_las_herramientas(modelo, tmp_path):
    from ptcg_agente import servidor_mcp as srv
    srv._estado.update(modelo=modelo, registro=Registro("claude-mcp", carpeta=tmp_path))
    nombres = {t.name for t in asyncio.run(srv.servidor.list_tools())}
    assert set(hz.HERRAMIENTAS) | {"verificar_respuesta"} <= nombres
    cur = _estados("final", modelo)[0]
    resultado = asyncio.run(srv.servidor.call_tool("estimar_probabilidad", {"observacion": cur}))
    datos = resultado.structured_content if hasattr(resultado, "structured_content") else None
    datos = datos or json.loads(resultado.content[0].text)
    datos = datos.get("result", datos)
    assert datos["ok"] and datos["verificacion"]["aprobado"]
    texto = f"Probabilidad de victoria: {datos['probabilidad_texto']}."
    verif = asyncio.run(srv.servidor.call_tool("verificar_respuesta", {"texto": texto}))
    v = verif.structured_content if hasattr(verif, "structured_content") else None
    v = v or json.loads(verif.content[0].text)
    assert v.get("result", v)["aprobado"]


def test_verificador_acepta_ids_de_archivo_signos_y_promesas_negadas(modelo, tmp_path):
    """Falsos positivos vistos con Claude: id de partida, menos tipografico y 'no garantiza'."""
    g = _partidas(1)[0]
    rep = tmp_path / "partida_87406956.json"
    rep.write_text(json.dumps(g), encoding="utf-8")
    s = hz.llamar(modelo, "evaluar_partida", {"archivo": str(rep)})
    giro = s["puntos_de_giro"][0]
    cambio = round(100 * giro["cambio"], 1)
    texto = (f"Partida 87406956: en el paso {giro['paso']} la probabilidad cambia "
             f"−{abs(cambio)} puntos; luego cae {abs(cambio)} puntos. Es una estimacion que "
             "no garantiza el resultado.")
    r = verificar_texto(texto, [s])
    assert r["aprobado"], r["problemas"]
    assert not verificar_texto("Esto garantiza la victoria.", [s])["aprobado"]
    assert not verificar_texto("Cambia −99.9 puntos.", [s])["aprobado"]