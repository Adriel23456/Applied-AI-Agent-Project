"""Servidor local del simulador. Toda probabilidad sale de las herramientas del agente
(herramientas.llamar), asi que pasa por la revision de dominio y el verificador igual que en
las respuestas del agente.

API (JSON):
  GET  /                      la pagina del simulador
  GET  /api/inicio            estado inicial: observacion, partida cargada y ejemplos
  POST /api/evaluar           {"observacion": {...}} -> probabilidad, SHAP, advertencias, verificacion
  POST /api/partida           {"archivo": "..."} -> curva, turnos, puntos de giro y pasos con observacion
  GET  /api/paso?n=PASO       observacion del jugador que actua en ese paso de la partida cargada
  GET  /api/vacio             estado nuevo, sin partida, para armarlo desde cero
  GET  /api/catalogo          cartas que se pueden poner en juego (vistas en entrenamiento)
"""

import json
import threading
import webbrowser
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ptcg_agente import cartas
from ptcg_agente import herramientas as hz
from ptcg_agente.artefactos import ARTEFACTOS_DIR
from ptcg_agente.entradas import EntradaInvalida, leer_json, observacion_de_paso
from ptcg_wp.features import acting_player

WEB = Path(__file__).resolve().parent / "web"
TOP_SHAP = 8


class Simulador:
    """Estado del simulador: el modelo, la partida cargada y el registro de invocaciones."""

    def __init__(self, modelo, registro=None, observacion=None, archivo=None, paso=None):
        self.modelo = modelo
        self.registro = registro
        self.repeticion = None
        self.archivo = None
        self.inicial = observacion
        self.paso_inicial = None
        if archivo is not None:
            self.cargar_partida(archivo)
            if self.inicial is None:
                self.paso_inicial = paso if paso is not None else self.pasos_con_observacion()[0]
                self.inicial = observacion_de_paso(self.repeticion, self.paso_inicial)

    def pasos_con_observacion(self):
        pasos = []
        for i, paso in enumerate(self.repeticion["steps"]):
            j = acting_player(paso)
            if j is not None and (paso[j].get("observation") or {}).get("current"):
                pasos.append(i)
        return pasos

    def cargar_partida(self, archivo):
        datos = leer_json(archivo)
        if not isinstance(datos, dict) or "steps" not in datos:
            raise EntradaInvalida("el archivo no es una repeticion completa (falta 'steps')")
        self.repeticion, self.archivo = datos, str(archivo)
        curva = hz.llamar(self.modelo, "evaluar_partida", {"archivo": str(archivo)}, self.registro,
                          agente="simulador")
        return {**curva, "archivo": Path(archivo).name, "pasos": self.pasos_con_observacion()}

    def evaluar(self, observacion):
        return hz.llamar(self.modelo, "explicar_prediccion", {"observacion": observacion, "top": TOP_SHAP},
                         self.registro, agente="simulador")

    def paso(self, n):
        if self.repeticion is None:
            raise EntradaInvalida("no hay una partida cargada")
        return {"paso": n, "observacion": observacion_de_paso(self.repeticion, n)}

    def catalogo(self):
        """Cartas que se pueden poner en juego: todas las vistas como activo en el entrenamiento,
        con sus PV maximos del catalogo agente/cartas.json. Si el catalogo no esta, los PV salen
        de las repeticiones disponibles (solo de las cartas que aparecen en ellas)."""
        if getattr(self, "_catalogo", None) is None:
            vistas = set(self.modelo.perfil.get("cartas_activas", []))
            pv, nombres = {}, {}
            ruta = ARTEFACTOS_DIR / cartas.RUTA
            if ruta.exists():
                for c in json.loads(ruta.read_text(encoding="utf-8"))["cartas"]:
                    pv[c["id"]] = Counter({c["maxHp"]: 1})
            else:
                for archivo in self.ejemplos() + ([self.archivo] if self.archivo else []):
                    try:
                        rep = leer_json(archivo)
                    except EntradaInvalida:
                        continue
                    for paso in rep.get("steps", []):
                        for entrada in paso:
                            cur = (entrada.get("observation") or {}).get("current") or {}
                            for jugador in cur.get("players") or []:
                                for m in [x for x in (jugador.get("active") or []) + (jugador.get("bench") or []) if x]:
                                    if isinstance(m.get("id"), int) and isinstance(m.get("maxHp"), int):
                                        pv.setdefault(m["id"], Counter())[m["maxHp"]] += 1
                                        if m.get("name"):
                                            nombres[m["id"]] = m["name"]
            cartas_vistas = [{"id": c, "maxHp": pv[c].most_common(1)[0][0] if c in pv else None,
                              "nombre": nombres.get(c)} for c in sorted(vistas)]
            self._catalogo = sorted(cartas_vistas, key=lambda c: (c["maxHp"] is None, c["id"]))
        return self._catalogo

    def vacio(self):
        """Estado nuevo, sin partida y sin nada en la mesa: turno 0, sin premios, mano, mazo,
        descarte ni Pokemon. El usuario lo arma desde cero. Mientras sea turno 0, no haya premios
        por tomar o algun jugador no tenga Pokemon en juego, el modelo no da probabilidad."""
        def jugador():
            j = {"deckCount": 0, "handCount": 0, "discard": [], "prize": [], "active": [], "bench": []}
            j.update({f: False for f in ("asleep", "burned", "confused", "paralyzed", "poisoned")})
            return j

        return {"players": [jugador(), jugador()], "yourIndex": 0, "turn": 0, "firstPlayer": 0,
                "turnActionCount": 0, "energyAttached": False, "retreated": False, "supporterPlayed": False,
                "stadiumPlayed": False, "stadium": None}

    def ejemplos(self):
        carpeta = ARTEFACTOS_DIR / "agente" / "ejemplos"
        return [str(p) for p in sorted(carpeta.glob("partida_*.json"))]


def _manejador(sim):
    class Manejador(BaseHTTPRequestHandler):
        def log_message(self, formato, *args):  # silencioso: el registro JSONL ya guarda cada llamada
            pass

        def _responder(self, codigo, cuerpo, tipo="application/json"):
            datos = cuerpo if isinstance(cuerpo, bytes) else json.dumps(cuerpo, default=str).encode("utf-8")
            self.send_response(codigo)
            self.send_header("Content-Type", f"{tipo}; charset=utf-8")
            self.send_header("Content-Length", str(len(datos)))
            self.end_headers()
            self.wfile.write(datos)

        def _json(self):
            largo = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(largo) or b"{}")

        def _seguro(self, funcion):
            try:
                self._responder(200, funcion())
            except (EntradaInvalida, ValueError, KeyError) as e:
                self._responder(400, {"ok": False, "error": str(e)})

        def do_GET(self):
            url = urlparse(self.path)
            if url.path in ("/", "/index.html"):
                self._responder(200, (WEB / "index.html").read_bytes(), "text/html")
            elif url.path == "/api/inicio":
                partida = sim.cargar_partida(sim.archivo) if sim.archivo else None
                self._seguro(lambda: {"observacion": sim.inicial, "paso": sim.paso_inicial, "partida": partida,
                                     "ejemplos": sim.ejemplos()})
            elif url.path == "/api/vacio":
                self._seguro(lambda: {"observacion": sim.vacio()})
            elif url.path == "/api/catalogo":
                self._seguro(lambda: {"cartas": sim.catalogo()})
            elif url.path == "/api/paso":
                n = int(parse_qs(url.query).get("n", ["-1"])[0])
                self._seguro(lambda: sim.paso(n))
            else:
                self._responder(404, {"ok": False, "error": "no existe"})

        def do_POST(self):
            url = urlparse(self.path)
            if url.path == "/api/evaluar":
                self._seguro(lambda: sim.evaluar(self._json().get("observacion")))
            elif url.path == "/api/partida":
                self._seguro(lambda: sim.cargar_partida(self._json()["archivo"]))
            else:
                self._responder(404, {"ok": False, "error": "no existe"})

    return Manejador


def crear(modelo, registro=None, observacion=None, archivo=None, paso=None, puerto=8765):
    """Crea el servidor (sin arrancarlo). puerto=0 elige uno libre."""
    sim = Simulador(modelo, registro, observacion, archivo, paso)
    servidor = ThreadingHTTPServer(("127.0.0.1", puerto), _manejador(sim))
    servidor.simulador = sim
    return servidor


def url_de(servidor):
    return f"http://127.0.0.1:{servidor.server_address[1]}/"


def lanzar(modelo, registro=None, observacion=None, archivo=None, paso=None, puerto=0, abrir=True):
    """Arranca el simulador en segundo plano y devuelve (servidor, url). Lo usa abrir_simulador."""
    servidor = crear(modelo, registro, observacion, archivo, paso, puerto)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    url = url_de(servidor)
    if abrir:
        webbrowser.open(url)
    return servidor, url