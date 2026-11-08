"""Simulador grafico (rama 08): la probabilidad que muestra es la del predictor, la API responde
a ediciones del estado y a la navegacion de una partida, y abrir_simulador lo lanza."""

import asyncio
import copy
import json
import sys
import threading
import urllib.request
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ptcg_agente.simulador import servidor as sv  # noqa: E402
from test_agente import _estados, _partidas, modelo, raiz  # noqa: E402,F401


def _get(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return r.read().decode("utf-8")


def _post(url, cuerpo):
    pedido = urllib.request.Request(url, data=json.dumps(cuerpo).encode("utf-8"),
                                    headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(pedido, timeout=10) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())


@pytest.fixture()
def simulador(modelo, tmp_path):  # noqa: F811
    partida = _partidas(1)[0]
    archivo = tmp_path / "partida.json"
    archivo.write_text(json.dumps(partida), encoding="utf-8")
    servidor = sv.crear(modelo, archivo=str(archivo), puerto=0)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    yield sv.url_de(servidor), partida, archivo
    servidor.shutdown()


def test_pagina_e_inicio(simulador):
    url, partida, _ = simulador
    assert "Simulador de probabilidad de victoria" in _get(url)
    inicio = json.loads(_get(url + "api/inicio"))
    assert inicio["partida"]["curva"] and inicio["partida"]["pasos"]
    assert inicio["paso"] == inicio["partida"]["pasos"][0] and inicio["observacion"]["turn"] == 0


def test_probabilidad_igual_al_predictor_y_responde_a_ediciones(simulador, modelo):  # noqa: F811
    url, _, _ = simulador
    cur = _estados("final", modelo)[0]
    r = _post(url + "api/evaluar", {"observacion": cur})
    assert r["ok"] and r["verificacion"]["aprobado"]
    assert r["probabilidad"] == pytest.approx(modelo.predictor.probabilidad(cur), abs=1e-12)
    assert r["a_favor"] or r["en_contra"]
    editado = copy.deepcopy(cur)
    editado["players"][1 - cur["yourIndex"]]["deckCount"] = 0
    r2 = _post(url + "api/evaluar", {"observacion": editado})
    assert r2["probabilidad"] == pytest.approx(modelo.predictor.probabilidad(editado), abs=1e-12)
    sin_premios = copy.deepcopy(cur)
    sin_premios["players"][cur["yourIndex"]]["prize"] = []
    r3 = _post(url + "api/evaluar", {"observacion": sin_premios})
    assert r3["probabilidad"] is None and "sin_prediccion" in [a["codigo"] for a in r3["advertencias"]]
    malo = _post(url + "api/evaluar", {"observacion": {"turn": 3}})
    assert malo["ok"] is False and "faltan campos" in malo["error"]


def test_navegacion_de_la_partida(simulador, modelo):  # noqa: F811
    url, partida, archivo = simulador
    cargada = _post(url + "api/partida", {"archivo": str(archivo)})
    for punto in cargada["curva"][:5]:
        paso = json.loads(_get(url + f"api/paso?n={punto['paso']}"))
        p = modelo.predictor.probabilidad(paso["observacion"])
        assert punto["p_jugador0"] == pytest.approx(p if paso["observacion"]["yourIndex"] == 0 else 1 - p, abs=1e-4)
    with pytest.raises(urllib.error.HTTPError):
        _get(url + "api/paso?n=999999")
    assert _post(url + "api/partida", {"archivo": str(archivo.parent / "no_existe.json")})["ok"] is False


def test_abrir_simulador_lanza_y_devuelve_la_url(modelo, tmp_path):  # noqa: F811
    from ptcg_agente.herramientas import abrir_simulador
    archivo = tmp_path / "partida.json"
    archivo.write_text(json.dumps(_partidas(1)[0]), encoding="utf-8")
    s = abrir_simulador.ejecutar(modelo, archivo=str(archivo), paso=5, abrir=False)
    assert s["ok"] and s["url"].startswith("http://127.0.0.1:")
    assert json.loads(_get(s["url"] + "api/inicio"))["paso"] == 5
    obs = tmp_path / "estado.json"
    obs.write_text(json.dumps(_estados("medio", modelo)[0]), encoding="utf-8")
    s2 = abrir_simulador.ejecutar(modelo, archivo=str(obs), abrir=False)
    assert json.loads(_get(s2["url"] + "api/inicio"))["observacion"]["turn"] > 0


def test_servidor_mcp_expone_abrir_simulador(modelo, tmp_path, monkeypatch):  # noqa: F811
    from ptcg_agente import servidor_mcp as srv
    from ptcg_agente.registro import Registro
    srv._estado.update(modelo=modelo, registro=Registro("claude-mcp", carpeta=tmp_path))
    assert "abrir_simulador" in {t.name for t in asyncio.run(srv.servidor.list_tools())}
    monkeypatch.setattr(sv.webbrowser, "open", lambda url: True)
    archivo = tmp_path / "partida.json"
    archivo.write_text(json.dumps(_partidas(1)[0]), encoding="utf-8")
    r = asyncio.run(srv.servidor.call_tool("abrir_simulador", {"archivo": str(archivo)}))
    datos = r.structured_content if hasattr(r, "structured_content") else None
    datos = datos or json.loads(r.content[0].text)
    assert datos.get("result", datos)["ok"]


def test_estado_nuevo_sin_partida_se_evalua(simulador, modelo):  # noqa: F811
    url, _, _ = simulador
    cartas = json.loads(_get(url + "api/catalogo"))["cartas"]
    assert cartas and {c["id"] for c in cartas} <= set(modelo.perfil["cartas_activas"])
    assert any(c["maxHp"] for c in cartas)  # los PV salen de las repeticiones disponibles
    vacio = json.loads(_get(url + "api/vacio"))["observacion"]
    r = _post(url + "api/evaluar", {"observacion": vacio})
    assert r["ok"] and r["probabilidad"] is not None and r["verificacion"]["aprobado"]
    assert r["probabilidad"] == pytest.approx(modelo.predictor.probabilidad(vacio), abs=1e-12)
    actua_1 = copy.deepcopy(vacio)
    actua_1["yourIndex"] = 1
    r1 = _post(url + "api/evaluar", {"observacion": actua_1})
    assert r1["ok"] and r1["jugador"] == 1


def test_abrir_simulador_vacio(modelo):  # noqa: F811
    from ptcg_agente.herramientas import abrir_simulador
    s = abrir_simulador.ejecutar(modelo, vacio=True, abrir=False)
    inicio = json.loads(_get(s["url"] + "api/inicio"))
    assert inicio["partida"] is None and inicio["observacion"]["turn"] == 3