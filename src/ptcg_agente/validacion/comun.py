"""Piezas comunes de la bateria N1.

Cada caso del protocolo deja UNA fila en resultados:
  caso, grupo, descripcion, esperado, obtenido, aprobado (True, False o None = solo registro),
  excepcion (True si algo se cayo sin control) y duracion_ms.
Cada estado evaluado deja una fila en detalle (probabilidad, advertencias, verificacion), y cada
llamada a una herramienta deja su latencia.
"""

import copy
import time
import traceback

from ptcg_agente import herramientas as hz


class Bateria:
    def __init__(self, modelo, registro=None):
        self.modelo = modelo
        self.registro = registro
        self.resultados = []
        self.detalle = []
        self.latencias = []

    def llamar(self, nombre, **argumentos):
        inicio = time.perf_counter()
        salida = hz.llamar(self.modelo, nombre, argumentos, self.registro, agente="validacion")
        self.latencias.append({"herramienta": nombre, "ms": 1000 * (time.perf_counter() - inicio)})
        return salida

    def caso(self, caso, grupo, descripcion, esperado, funcion):
        """funcion() devuelve (obtenido, aprobado). Una excepcion cuenta como caso fallido."""
        inicio = time.perf_counter()
        excepcion = False
        try:
            obtenido, aprobado = funcion()
        except Exception as e:  # la robustez es justamente lo que se mide
            obtenido = f"excepcion: {type(e).__name__}: {e} | {traceback.format_exc(limit=2)[-300:]}"
            aprobado, excepcion = False, True
        self.resultados.append({"caso": caso, "grupo": grupo, "descripcion": descripcion,
                                "esperado": esperado, "obtenido": str(obtenido), "aprobado": aprobado,
                                "excepcion": excepcion,
                                "duracion_ms": round(1000 * (time.perf_counter() - inicio), 1)})

    def anotar_estado(self, caso, fila, salida, extra=None):
        self.detalle.append({
            "caso": caso, "grupo": fila.get("grupo"), "etapa": fila.get("stage"), "y": fila.get("y"),
            "p_tabla": fila.get("p"), "ok": salida.get("ok"), "p": salida.get("probabilidad"),
            "advertencias": ",".join(codigos(salida)),
            "verificado": salida.get("verificacion", {}).get("aprobado"), **(extra or {})})


def codigos(salida):
    return [a["codigo"] for a in salida.get("advertencias", [])]


def verificada(salida):
    return bool(salida.get("ok")) and salida["verificacion"]["aprobado"]


def copia(cur):
    return copy.deepcopy(cur)


def propio(cur):
    return cur["players"][cur["yourIndex"]]


def rival(cur):
    return cur["players"][1 - cur["yourIndex"]]


def activo(jugador):
    activos = [m for m in (jugador.get("active") or []) if m]
    return activos[0] if activos else None


def banca(jugador):
    return [m for m in (jugador.get("bench") or []) if m]


def texto_p(p):
    return "None" if p is None else f"{100 * p:.1f} %"


def direccion(antes, despues):
    if antes is None or despues is None:
        return "sin comparacion"
    if abs(despues - antes) < 0.005:
        return "casi igual"
    return "sube" if despues > antes else "baja"


def proporcion(n, total):
    return f"{n}/{total}"