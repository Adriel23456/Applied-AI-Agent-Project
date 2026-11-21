"""Entradas de las herramientas: de lo que manda el usuario a la observacion del jugador que actua.

Se aceptan tres formas:
  - observacion: el diccionario observation["current"] (o la observacion con la clave "current").
  - archivo de observacion: un .json con ese mismo contenido.
  - repeticion completa: un .json de Kaggle con "steps"; se elige el paso con 'paso'.

Toda entrada se valida aqui. Si algo no tiene el formato del juego, se lanza EntradaInvalida
con un mensaje para el usuario; las herramientas la convierten en una respuesta de error.
"""

import json
from pathlib import Path

from ptcg_wp.features import acting_player

CLAVES_CURRENT = ("players", "yourIndex", "turn", "firstPlayer", "turnActionCount")
CLAVES_JUGADOR = ("deckCount", "handCount")


class EntradaInvalida(ValueError):
    """La entrada no tiene el formato de una observacion del juego."""


def leer_json(archivo):
    ruta = Path(archivo).expanduser()
    if not ruta.is_file():
        raise EntradaInvalida(f"no existe el archivo {ruta}")
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise EntradaInvalida(f"{ruta.name} no es un JSON valido: {e}") from e


def es_repeticion(datos):
    return isinstance(datos, dict) and isinstance(datos.get("steps"), list)


def validar_current(cur):
    """Revisa que la observacion tenga lo que el extractor necesita. Devuelve cur."""
    if not isinstance(cur, dict):
        raise EntradaInvalida("la observacion debe ser un objeto JSON")
    if "current" in cur:
        cur = cur["current"]
        if not isinstance(cur, dict):
            raise EntradaInvalida("'current' esta vacio: es la vista del jugador que espera, "
                                  "no la del jugador que actua")
    faltan = [k for k in CLAVES_CURRENT if k not in cur]
    if faltan:
        raise EntradaInvalida(f"a la observacion le faltan campos: {faltan}")
    jugadores = cur["players"]
    if not isinstance(jugadores, list) or len(jugadores) != 2:
        raise EntradaInvalida("'players' debe tener exactamente dos jugadores")
    if cur["yourIndex"] not in (0, 1):
        raise EntradaInvalida("'yourIndex' debe ser 0 o 1")
    if not isinstance(cur["turn"], int) or cur["turn"] < 0:
        raise EntradaInvalida("'turn' debe ser un entero mayor o igual que 0")
    for k, p in enumerate(jugadores):
        if not isinstance(p, dict):
            raise EntradaInvalida(f"el jugador {k} no es un objeto")
        faltan = [c for c in CLAVES_JUGADOR if c not in p]
        if faltan:
            raise EntradaInvalida(f"al jugador {k} le faltan campos: {faltan}")
        for c in CLAVES_JUGADOR:
            if not isinstance(p[c], int) or p[c] < 0:
                raise EntradaInvalida(f"jugador {k}: '{c}' debe ser un entero no negativo")
    return cur


def observacion_de_paso(repeticion, paso):
    """Observacion del jugador que actua en el paso indicado de una repeticion."""
    pasos = repeticion["steps"]
    if not isinstance(paso, int) or not 0 <= paso < len(pasos):
        raise EntradaInvalida(f"'paso' debe estar entre 0 y {len(pasos) - 1}")
    j = acting_player(pasos[paso])
    if j is None:
        raise EntradaInvalida(f"en el paso {paso} ningun jugador esta actuando")
    cur = (pasos[paso][j].get("observation") or {}).get("current")
    if not cur:
        raise EntradaInvalida(f"el paso {paso} no trae la observacion del jugador que actua")
    return validar_current(cur)


def resolver(observacion=None, archivo=None, paso=None):
    """Devuelve (cur, origen). 'origen' describe de donde salio la observacion (para el registro)."""
    if (observacion is None) == (archivo is None):
        raise EntradaInvalida("indica 'observacion' o 'archivo' (uno de los dos)")
    if archivo is not None:
        datos = leer_json(archivo)
        nombre = Path(archivo).name
    else:
        datos, nombre = observacion, "observacion"
    if es_repeticion(datos):
        if paso is None:
            raise EntradaInvalida("es una repeticion completa: indica 'paso' (o usa evaluar_partida)")
        return observacion_de_paso(datos, paso), f"{nombre}#paso{paso}"
    return validar_current(datos), nombre


def resolver_repeticion(repeticion=None, archivo=None):
    """Repeticion completa (diccionario con 'steps') desde un objeto o un archivo."""
    if (repeticion is None) == (archivo is None):
        raise EntradaInvalida("indica 'repeticion' o 'archivo' (uno de los dos)")
    datos = leer_json(archivo) if archivo is not None else repeticion
    if not es_repeticion(datos):
        raise EntradaInvalida("no es una repeticion completa: falta la lista 'steps'")
    return datos, (Path(archivo).name if archivo is not None else "repeticion")